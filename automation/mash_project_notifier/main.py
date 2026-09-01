from __future__ import annotations

import argparse
import json
import sys
from datetime import date, datetime, timedelta, timezone
from typing import Any
from zoneinfo import ZoneInfo

from .config import ConfigurationError, Settings
from .deduplication import decode_state, encode_state
from .event_detector import detect_calendar_events, detect_status_events, event_key
from .github_client import GitHubClient, GitHubAPIError
from .message_renderer import render_calendar_event, render_daily_summary, render_pr_event, render_task_event
from .notifier import find_state_comment, publish_and_verify, save_state_and_verify
from .project_reader import ProjectDataError, read_project
from .repository_reader import link_pull_request_to_issue, read_pull_requests
from .sprint_metrics import MetricsError, calculate_sprint_metrics, locate_current_and_next_sprint

DONE_NAME = "Done"


def _done_option_id(project: dict[str, Any]) -> str:
    options = (project.get("status_field") or {}).get("options") or []
    for option in options:
        if option.get("name") == DONE_NAME and option.get("id"):
            return str(option["id"])
    raise MetricsError("Project Status field has no Done option")


def _item_map(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {str(item["item_id"]): item for item in items}


def _snapshot_items(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {
        str(item["item_id"]): {
            "status_id": item.get("status_id"),
            "status_name": item.get("status_name"),
            "sprint": item.get("sprint"),
            "number": item.get("number"),
            "title": item.get("title"),
            "url": item.get("url"),
            "repository": item.get("repository"),
        }
        for item in items
    }


def _date_label(today: date) -> str:
    return today.strftime("%d/%m/%Y")


def build_run_plan(
    project: dict[str, Any],
    today: date,
    previous_state: dict[str, Any] | None,
    *,
    daily: bool,
) -> dict[str, Any]:
    """Build all metrics and unsent non-PR events without writing anywhere."""
    previous = previous_state or {}
    items = project.get("items") or []
    current_items = _item_map(items)
    done_id = _done_option_id(project)
    calendar = locate_current_and_next_sprint(project.get("iterations") or [], today)
    current = calendar.get("current")
    if not current:
        raise MetricsError("no current Sprint for the supplied date")
    current_metrics = calculate_sprint_metrics(items, current["title"], done_id)
    previous_items = previous.get("items") or {}
    status_events = detect_status_events(previous_items, current_items, done_id)
    calendar_events = detect_calendar_events(calendar, current_metrics, today, daily=daily)
    if not previous_items:
        # Initialization must not replay historical start/completion/countdown events.
        calendar_events = [event for event in calendar_events if event["kind"] == "daily_summary"]
    sent_keys = {str(key) for key in previous.get("sent_keys") or []}
    events = [event for event in [*status_events, *calendar_events] if event.get("event_key") not in sent_keys]
    snapshot = {
        "version": 1,
        "items": _snapshot_items(items),
        "sent_keys": sorted(sent_keys | {str(event["event_key"]) for event in events}),
    }
    return {
        "baseline": not bool(previous_items),
        "data_quality": project.get("data_quality", "invalid"),
        "project": project.get("project") or {},
        "metrics": current_metrics,
        "calendar": calendar,
        "events": events,
        "snapshot": snapshot,
        "date_label": _date_label(today),
    }


def _pr_events(
    pull_requests: list[dict[str, Any]],
    project_items: dict[str, dict[str, Any]],
    sent_keys: set[str],
) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for pr in pull_requests:
        if not pr.get("merged_at"):
            continue
        links = link_pull_request_to_issue(pr)
        planning_links = [link for link in links if link["repository"] == "conloq/mash"]
        if not planning_links:
            continue
        # One PR is one evidence event; list the first explicit planning Issue as target.
        link = planning_links[0]
        item = next(
            (
                value
                for value in project_items.values()
                if value.get("repository") == link["repository"] and value.get("number") == link["number"]
            ),
            None,
        )
        if not item:
            continue
        key = f"pr_merged:{pr.get('repository')}:{pr.get('number')}:{pr.get('merged_at')}"
        if key in sent_keys:
            continue
        event = {
            "kind": "pr_merged",
            "event_key": key,
            "repository": pr.get("repository"),
            "number": pr.get("number"),
            "title": pr.get("title"),
            "url": pr.get("url"),
            "linked_issue": f"{link['repository']}#{link['number']}",
            "target_repository": link["repository"],
            "target_issue_number": link["number"],
        }
        events.append(event)
    return events


def render_event(event: dict[str, Any], plan: dict[str, Any]) -> str:
    kind = event.get("kind")
    if kind in {"task_done", "task_reopened"}:
        return render_task_event(event)
    if kind == "daily_summary":
        return render_daily_summary(
            plan["metrics"],
            plan["calendar"]["current"],
            plan["calendar"].get("next"),
            plan["date_label"],
        ) + "\n\n" + event_marker_for(event)
    if kind == "pr_merged":
        return render_pr_event(event)
    return render_calendar_event(event)


def event_marker_for(event: dict[str, Any]) -> str:
    from .deduplication import event_marker

    return event_marker(str(event["event_key"]))


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _is_daily_window(now_local: datetime, daily_hour: int) -> bool:
    return now_local.hour == daily_hour and now_local.minute < 15


def _load_state(client: GitHubClient, settings: Settings) -> tuple[dict[str, Any], dict[str, Any] | None]:
    if not settings.tracker_issue_number:
        return {}, None
    state, comment = find_state_comment(client, settings.tracker_repository, settings.tracker_issue_number)
    return state or {}, comment


def _safe_summary(plan: dict[str, Any], events: list[dict[str, Any]], settings: Settings, *, error: str | None = None) -> dict[str, Any]:
    result = {
        "settings": settings.safe_for_log(),
        "baseline": plan.get("baseline"),
        "data_quality": plan.get("data_quality"),
        "metrics": plan.get("metrics"),
        "calendar": plan.get("calendar"),
        "event_count": len(events),
        "event_kinds": [event.get("kind") for event in events],
        "dry_run": settings.dry_run,
    }
    if error:
        result["error"] = error
    return result


def run(settings: Settings | None = None, *, today: date | None = None, force_daily: bool = False) -> int:
    settings = settings or Settings.from_env()
    try:
        token = settings.require_token()
        client = GitHubClient(token)
        now_local = datetime.now(ZoneInfo(settings.timezone))
        today = today or now_local.date()
        daily = force_daily or _is_daily_window(now_local, settings.daily_hour)
        project = read_project(client, settings.project_id)
        previous, state_comment = _load_state(client, settings)
        plan = build_run_plan(project, today, previous, daily=daily)
        if plan["data_quality"] != "ok" and not settings.dry_run:
            raise ProjectDataError("Project data is partial; live notifications are disabled")
        sent_keys = {str(key) for key in previous.get("sent_keys") or []}
        if previous.get("last_pr_scan"):
            prs = read_pull_requests(client, settings.code_repositories, previous["last_pr_scan"])
            pr_events = _pr_events(prs, _item_map(project["items"]), sent_keys)
        else:
            pr_events = []
        events = [*plan["events"], *pr_events]
        events = [event for event in events if event.get("event_key") not in sent_keys]
        if settings.dry_run:
            print(json.dumps({**_safe_summary(plan, events, settings), "messages": [render_event(event, plan) for event in events]}, ensure_ascii=False, indent=2))
            return 0
        if not settings.tracker_issue_number:
            raise SettingsError("MASH_TRACKER_ISSUE_NUMBER is required for live notifications")
        delivered = set(sent_keys)
        published: list[dict[str, Any]] = []
        for event in events:
            target = _target_for_event(event, settings)
            if not target:
                raise SettingsError(f"no notification target for {event.get('kind')}")
            repository, issue_number = target
            result = publish_and_verify(client, repository, issue_number, render_event(event, plan))
            delivered.add(str(event["event_key"]))
            published.append(result)
        new_state = {
            **plan["snapshot"],
            "sent_keys": sorted(delivered),
            "last_pr_scan": _now_utc().isoformat(),
            "updated_at": _now_utc().isoformat(),
        }
        state_result = save_state_and_verify(
            client,
            settings.tracker_repository,
            settings.tracker_issue_number,
            new_state,
            state_comment,
        )
        print(json.dumps({**_safe_summary(plan, events, settings), "published": published, "state": state_result}, ensure_ascii=False, indent=2))
        return 0
    except (ConfigurationError, SettingsError, ProjectDataError, MetricsError, GitHubAPIError) as exc:
        print(json.dumps({"status": "not_verified", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


class SettingsError(ValueError):
    pass


def _target_for_event(event: dict[str, Any], settings: Settings) -> tuple[str, int] | None:
    from .notifier import target_for_event

    return target_for_event(
        event,
        tracker_repository=settings.tracker_repository,
        tracker_issue_number=settings.tracker_issue_number,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Central Mash Project notification reconciler")
    parser.add_argument("--dry-run", action="store_true", help="calculate and print messages without writing")
    parser.add_argument("--daily", action="store_true", help="force the daily summary event")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        settings = Settings.from_env()
    except ConfigurationError as exc:
        print(json.dumps({"status": "not_verified", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2
    if args.dry_run:
        settings = Settings(**{**settings.__dict__, "dry_run": True})
    return run(settings, force_daily=args.daily)


if __name__ == "__main__":
    raise SystemExit(main())
