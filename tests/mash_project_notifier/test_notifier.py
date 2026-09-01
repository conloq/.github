import pytest

from automation.mash_project_notifier.notifier import (
    find_state_comment,
    publish_and_verify,
    save_state_and_verify,
    target_for_event,
)


class FakeClient:
    def __init__(self):
        self.comments = []
        self.next_id = 1
        self.calls = []

    def create_comment(self, repository, issue_number, body):
        comment = {"id": self.next_id, "html_url": "https://github.com/comment/1", "body": body}
        self.next_id += 1
        self.comments.append(comment)
        self.calls.append(("create", repository, issue_number, body))
        return comment

    def update_comment(self, repository, comment_id, body):
        for comment in self.comments:
            if comment["id"] == comment_id:
                comment["body"] = body
                self.calls.append(("update", repository, comment_id, body))
                return comment
        raise AssertionError("comment not found")

    def list_comments(self, repository, issue_number):
        self.calls.append(("list", repository, issue_number))
        return list(self.comments)


def test_target_for_event_uses_source_issue_for_task_and_tracker_for_calendar():
    task_target = target_for_event(
        {"kind": "task_done", "repository": "conloq/mash", "number": 34},
        tracker_repository="conloq/.github",
        tracker_issue_number=7,
    )
    sprint_target = target_for_event(
        {"kind": "sprint_started"},
        tracker_repository="conloq/.github",
        tracker_issue_number=7,
    )

    assert task_target == ("conloq/mash", 34)
    assert sprint_target == ("conloq/.github", 7)


def test_publish_and_verify_reads_created_comment_back():
    client = FakeClient()

    result = publish_and_verify(client, "conloq/mash", 34, "@conloq/mash\n\n✅ concluída")

    assert result["verified"] is True
    assert client.calls == [
        ("create", "conloq/mash", 34, "@conloq/mash\n\n✅ concluída"),
        ("list", "conloq/mash", 34),
    ]


def test_state_comment_is_found_and_updated_without_creating_another_state_comment():
    client = FakeClient()
    client.create_comment("conloq/.github", 7, "<!-- mash-notifier-state:v1 -->\n```json\n{\"version\":1}\n```")

    state, comment = find_state_comment(client, "conloq/.github", 7)
    result = save_state_and_verify(
        client,
        "conloq/.github",
        7,
        {"version": 1, "sent_keys": ["one"]},
        comment,
    )

    assert state == {"version": 1}
    assert result["verified"] is True
    assert [call[0] for call in client.calls if call[0] in {"create", "update"}] == ["create", "update"]
