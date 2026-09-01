from __future__ import annotations

from datetime import date
from typing import Any


def event_key(event: dict[str, Any]) -> str:
    """Build a deterministic key for a status transition or calendar event."""
    kind = str(event.get("kind") or "event")
    if kind in {"task_done", "task_reopened"}:
        return ":".join(
            [
                kind,
                str(event.get("item_id") or "unknown"),
                str(event.get("old_status_id") or "unknown"),
                str(event.get("new_status_id") or "unknown"),
            ]
        )
    parts = [kind, str(event.get("target") or "unknown"), str(event.get("date") or "unknown")]
    if event.get("days") is not None:
        parts.append(str(event["days"]))
    return ":".join(parts)


def detect_status_events(
    previous: dict[str, dict[str, Any]],
    current: dict[str, dict[str, Any]],
    done_option_id: str,
) -> list[dict[str, Any]]:
    """Detect only Done and re-open transitions.

    An empty previous snapshot intentionally emits no task events. This avoids
    notifying the whole team about historical states on first initialization.
    """
    if not previous:
        return []
    events: list[dict[str, Any]] = []
    for item_id in sorted(current):
        now = current[item_id]
        old = previous.get(item_id)
        if not old:
            continue
        old_id = str(old.get("status_id") or "")
        new_id = str(now.get("status_id") or "")
        if old_id == new_id:
            continue
        if new_id == str(done_option_id):
            kind = "task_done"
        elif old_id == str(done_option_id):
            kind = "task_reopened"
        else:
            continue
        event = {
            **now,
            "kind": kind,
            "item_id": item_id,
            "old_status_id": old_id,
            "old_status_name": old.get("status_name") or "(sem Status)",
            "new_status_id": new_id,
            "status_name": now.get("status_name") or "(sem Status)",
        }
        event["event_key"] = event_key(event)
        events.append(event)
    return events


def detect_calendar_events(
    calendar: dict[str, Any],
    current_metrics: dict[str, Any],
    today: date,
    *,
    daily: bool,
    thresholds: tuple[int, ...] = (3, 1),
) -> list[dict[str, Any]]:
    """Detect Sprint start, countdown, deadline, completion and daily events."""
    current = calendar.get("current")
    next_sprint = calendar.get("next")
    events: list[dict[str, Any]] = []
    today_text = today.isoformat()

    if current:
        title = str(current.get("title") or "")
        start = str(current.get("startDate") or "")
        end = str(current.get("endDate") or "")
        if start == today_text:
            events.append({"kind": "sprint_started", "target": title, "date": start, "sprint": title, "metrics": current_metrics})
        if daily:
            events.append({"kind": "daily_summary", "target": title, "date": today_text, "sprint": title, "metrics": current_metrics})
        if end:
            days_left = (date.fromisoformat(end) - today).days + 1
            if days_left in thresholds and current_metrics.get("remaining", 0) > 0:
                events.append(
                    {
                        "kind": "sprint_deadline",
                        "target": title,
                        "date": end,
                        "days": days_left,
                        "sprint": title,
                        "metrics": current_metrics,
                    }
                )
            if current_metrics.get("total", 0) > 0 and current_metrics.get("remaining", 0) == 0:
                events.append(
                    {
                        "kind": "sprint_completed",
                        "target": title,
                        "date": end,
                        "sprint": title,
                        "metrics": current_metrics,
                    }
                )

    if next_sprint:
        title = str(next_sprint.get("title") or "")
        start = str(next_sprint.get("startDate") or "")
        days = next_sprint.get("days_until_start")
        if days in thresholds:
            events.append(
                {
                    "kind": "next_sprint_threshold",
                    "target": title,
                    "date": start,
                    "days": days,
                    "sprint": title,
                }
            )
    for event in events:
        event["event_key"] = event_key(event)
    return events
