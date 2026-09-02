from automation.mash_project_notifier.message_renderer import (
    render_calendar_event,
    render_daily_summary,
    render_pr_event,
    render_task_event,
)


def test_render_task_event_mentions_team_and_preserves_repository_context():
    body = render_task_event(
        {
            "kind": "task_done",
            "number": 34,
            "title": "Implementar integração @outra-equipe",
            "repository": "conloq/mash",
            "url": "https://github.com/conloq/mash/issues/34",
            "sprint": "Sprint 2",
            "old_status_name": "In progress",
            "status_name": "Done",
            "event_key": "task_done:item-34:in-progress:done",
        }
    )

    assert "@conloq/mash" in body
    assert "#34" in body
    assert "conloq/mash" in body
    assert "Done" in body
    assert "@\u200boutra-equipe" in body


def test_render_daily_summary_reports_remaining_and_next_sprint():
    body = render_daily_summary(
        {
            "sprint": "Sprint 2",
            "total": 5,
            "done": 1,
            "remaining": 4,
            "status_counts": {"Backlog": 1, "Done": 1, "Ready": 3},
            "repository_counts": {"conloq/mash": 5},
        },
        {"title": "Sprint 2", "startDate": "2026-09-01", "endDate": "2026-09-15"},
        {"title": "Sprint 3", "startDate": "2026-09-16", "days_until_start": 15},
        "01/09/2026",
    )

    assert "Tarefas totais: 5" in body
    assert "Concluídas: 1" in body
    assert "Restantes: 4" in body
    assert "16/09/2026" in body
    assert "15 dias corridos" in body


def test_render_calendar_event_explains_next_sprint_threshold():
    body = render_calendar_event(
        {
            "kind": "next_sprint_threshold",
            "sprint": "Sprint 3",
            "date": "2026-09-16",
            "days": 3,
            "event_key": "next_sprint_threshold:Sprint 3:2026-09-16:3",
        }
    )

    assert "@conloq/mash" in body
    assert "Sprint 3" in body
    assert "3 dias corridos" in body
    assert "16/09/2026" in body


def test_render_pr_event_says_pr_is_evidence_not_an_extra_task():
    body = render_pr_event(
        {
            "repository": "conloq/Back-End",
            "number": 8,
            "title": "Implementar contrato de análise",
            "url": "https://github.com/conloq/Back-End/pull/8",
            "linked_issue": "conloq/mash#34",
            "event_key": "pr_merged:conloq/Back-End:8",
        }
    )

    assert "Pull Request mesclada" in body
    assert "conloq/Back-End" in body
    assert "conloq/mash#34" in body
    assert "não aumenta a contagem" in body
