from __future__ import annotations

from collections import Counter
from datetime import date, timedelta
from typing import Any, Iterable


class MetricsError(ValueError):
    """Raised when Project data cannot support a trustworthy count."""


def _sprint_title(item: dict[str, Any]) -> str | None:
    sprint = item.get("sprint")
    if isinstance(sprint, dict):
        return sprint.get("title") or sprint.get("name")
    return sprint


def calculate_sprint_metrics(
    items: Iterable[dict[str, Any]],
    sprint_title: str,
    done_option_id: str,
) -> dict[str, Any]:
    """Count unique Project cards assigned to one Sprint.

    A card is complete only when its status ID equals ``done_option_id``.
    Pull Requests and commits must not be passed as ``items`` here.
    """
    selected: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in items:
        if _sprint_title(item) != sprint_title:
            continue
        item_id = str(item.get("item_id") or item.get("id") or "")
        if not item_id:
            raise MetricsError("Project item without item_id")
        if item_id in seen:
            raise MetricsError(f"duplicate Project item_id: {item_id}")
        seen.add(item_id)
        selected.append(item)

    status_counts = Counter(str(item.get("status_name") or "(sem Status)") for item in selected)
    repository_counts = Counter(str(item.get("repository") or "(sem repositório)") for item in selected)
    done = sum(1 for item in selected if str(item.get("status_id") or "") == str(done_option_id))
    return {
        "sprint": sprint_title,
        "total": len(selected),
        "done": done,
        "remaining": len(selected) - done,
        "status_counts": dict(sorted(status_counts.items())),
        "repository_counts": dict(sorted(repository_counts.items())),
    }


def _normalise_iteration(iteration: dict[str, Any]) -> dict[str, Any]:
    title = iteration.get("title") or iteration.get("name")
    start = iteration.get("startDate") or iteration.get("start_date")
    duration = iteration.get("duration")
    if not title or not start or not duration:
        raise MetricsError(f"invalid Sprint iteration: {iteration!r}")
    try:
        start_date = date.fromisoformat(str(start))
        duration_days = int(duration)
    except (TypeError, ValueError) as exc:
        raise MetricsError(f"invalid Sprint date or duration: {iteration!r}") from exc
    if duration_days < 1:
        raise MetricsError(f"Sprint duration must be positive: {iteration!r}")
    end_date = start_date + timedelta(days=duration_days - 1)
    return {
        "id": iteration.get("id") or iteration.get("iterationId"),
        "title": str(title),
        "startDate": start_date.isoformat(),
        "endDate": end_date.isoformat(),
        "duration": duration_days,
    }


def locate_current_and_next_sprint(
    iterations: Iterable[dict[str, Any]],
    today: date,
) -> dict[str, Any]:
    """Return current/next Sprint and calendar distance in whole days."""
    normalised = [_normalise_iteration(iteration) for iteration in iterations]
    current = []
    future = []
    for iteration in normalised:
        start = date.fromisoformat(iteration["startDate"])
        end = date.fromisoformat(iteration["endDate"])
        if start <= today <= end:
            current.append(iteration)
        elif start > today:
            future.append(iteration)
    if len(current) > 1:
        raise MetricsError("more than one current Sprint")
    next_sprint = min(future, key=lambda value: value["startDate"], default=None)
    if next_sprint:
        next_sprint = {
            **next_sprint,
            "days_until_start": (date.fromisoformat(next_sprint["startDate"]) - today).days,
        }
    return {
        "current": current[0] if current else None,
        "next": next_sprint,
        "days_until_next": next_sprint["days_until_start"] if next_sprint else None,
    }
