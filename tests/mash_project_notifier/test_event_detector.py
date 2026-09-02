from datetime import date

from automation.mash_project_notifier.event_detector import detect_calendar_events


def calendar(current_start="2026-09-01", current_end="2026-09-15", next_start="2026-09-16", days_until=3):
    return {
        "current": {"title": "Sprint 2", "startDate": current_start, "endDate": current_end},
        "next": {"title": "Sprint 3", "startDate": next_start, "days_until_start": days_until},
        "days_until_next": days_until,
    }


def metrics(remaining=4):
    return {
        "sprint": "Sprint 2",
        "total": 5,
        "done": 5 - remaining,
        "remaining": remaining,
        "status_counts": {"Done": 5 - remaining, "Ready": remaining},
        "repository_counts": {"conloq/mash": 5},
    }


def test_detect_calendar_events_reports_three_day_next_sprint_and_deadline_alerts():
    events = detect_calendar_events(
        calendar(days_until=3),
        metrics(remaining=4),
        date(2026, 9, 13),
        daily=False,
    )

    assert {event["kind"] for event in events} == {"next_sprint_threshold", "sprint_deadline"}
    assert {event["days"] for event in events} == {3}


def test_detect_calendar_events_reports_sprint_start_and_daily_summary():
    events = detect_calendar_events(
        calendar(days_until=15),
        metrics(remaining=0),
        date(2026, 9, 1),
        daily=True,
    )

    assert {event["kind"] for event in events} == {"sprint_started", "daily_summary", "sprint_completed"}


def test_detect_calendar_events_does_not_report_deadline_when_nothing_remains():
    events = detect_calendar_events(
        calendar(current_end="2026-09-03", next_start="2026-09-04", days_until=1),
        metrics(remaining=0),
        date(2026, 9, 2),
        daily=False,
    )

    assert all(event["kind"] != "sprint_deadline" for event in events)
