from datetime import date

from automation.mash_project_notifier.sprint_metrics import (
    calculate_sprint_metrics,
    locate_current_and_next_sprint,
)


def test_calculate_sprint_metrics_counts_cards_once_and_breaks_down_status():
    items = [
        {"item_id": "item-1", "sprint": "Sprint 2", "status_id": "done", "status_name": "Done", "repository": "conloq/mash"},
        {"item_id": "item-2", "sprint": "Sprint 2", "status_id": "ready", "status_name": "Ready", "repository": "conloq/mash"},
        {"item_id": "item-3", "sprint": "Sprint 2", "status_id": "ready", "status_name": "Ready", "repository": "conloq/mash"},
        {"item_id": "item-4", "sprint": "Sprint 2", "status_id": "backlog", "status_name": "Backlog", "repository": "conloq/mash"},
        {"item_id": "item-5", "sprint": "Sprint 3", "status_id": "ready", "status_name": "Ready", "repository": "conloq/mash"},
    ]

    result = calculate_sprint_metrics(items, "Sprint 2", "done")

    assert result["total"] == 4
    assert result["done"] == 1
    assert result["remaining"] == 3
    assert result["status_counts"] == {"Backlog": 1, "Done": 1, "Ready": 2}
    assert result["repository_counts"] == {"conloq/mash": 4}


def test_locate_current_and_next_sprint_uses_calendar_dates():
    iterations = [
        {"title": "Sprint 2", "startDate": "2026-09-01", "duration": 15},
        {"title": "Sprint 3", "startDate": "2026-09-16", "duration": 15},
    ]

    result = locate_current_and_next_sprint(iterations, date(2026, 9, 1))

    assert result["current"]["title"] == "Sprint 2"
    assert result["current"]["endDate"] == "2026-09-15"
    assert result["next"]["title"] == "Sprint 3"
    assert result["days_until_next"] == 15
