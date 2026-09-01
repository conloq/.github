from datetime import date

from automation.mash_project_notifier.main import _pr_events, build_run_plan


def project(items):
    return {
        "project": {"id": "project-id", "title": "Mash", "number": 2},
        "status_field": {"id": "status-field", "name": "Status", "options": [{"id": "ready", "name": "Ready"}, {"id": "done", "name": "Done"}]},
        "iterations": [
            {"id": "s2", "title": "Sprint 2", "startDate": "2026-09-01", "duration": 15},
            {"id": "s3", "title": "Sprint 3", "startDate": "2026-09-16", "duration": 15},
        ],
        "items": items,
        "data_quality": "ok",
    }


def item(item_id, status_id, status_name):
    return {
        "item_id": item_id,
        "number": 34,
        "title": "Implementar integração",
        "url": "https://github.com/conloq/mash/issues/34",
        "repository": "conloq/mash",
        "status_id": status_id,
        "status_name": status_name,
        "sprint": "Sprint 2",
    }


def test_first_run_only_creates_baseline_and_daily_summary_when_requested():
    plan = build_run_plan(project([item("item-34", "ready", "Ready")]), date(2026, 9, 1), {}, daily=True)

    assert plan["metrics"]["remaining"] == 1
    assert [event["kind"] for event in plan["events"]] == ["daily_summary"]
    assert plan["baseline"] is True


def test_existing_snapshot_detects_done_transition_and_next_sprint_distance():
    previous = {
        "items": {"item-34": {"status_id": "ready", "status_name": "Ready", "sprint": "Sprint 2"}},
        "sent_keys": [
            "sprint_started:Sprint 2:2026-09-01",
            "sprint_completed:Sprint 2:2026-09-15",
        ],
    }

    plan = build_run_plan(project([item("item-34", "done", "Done")]), date(2026, 9, 1), previous, daily=False)

    assert plan["calendar"]["next"]["title"] == "Sprint 3"
    assert plan["calendar"]["days_until_next"] == 15
    assert [event["kind"] for event in plan["events"]] == ["task_done"]
    assert plan["events"][0]["event_key"] == "task_done:item-34:ready:done"


def test_backend_pr_is_evidence_for_planning_issue_without_changing_task_count():
    project_item = item("item-34", "ready", "Ready")
    pull_requests = [
        {
            "repository": "conloq/Back-End",
            "number": 8,
            "title": "Implementar contrato de análise",
            "body": "Closes conloq/mash#34",
            "url": "https://github.com/conloq/Back-End/pull/8",
            "merged_at": "2026-09-01T18:00:00Z",
        }
    ]

    events = _pr_events(pull_requests, {"item-34": project_item}, set())
    plan = build_run_plan(project([project_item]), date(2026, 9, 1), {"items": {"item-34": project_item}, "sent_keys": []}, daily=False)

    assert len(events) == 1
    assert events[0]["target_repository"] == "conloq/mash"
    assert events[0]["target_issue_number"] == 34
    assert plan["metrics"]["total"] == 1
    assert plan["metrics"]["remaining"] == 1


def test_unlinked_backend_pr_is_not_assigned_to_a_project_task():
    events = _pr_events(
        [{
            "repository": "conloq/Back-End",
            "number": 9,
            "title": "Refatorar código",
            "body": "Sem referência de Issue",
            "merged_at": "2026-09-01T18:00:00Z",
        }],
        {},
        set(),
    )

    assert events == []
