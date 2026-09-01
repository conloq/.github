from __future__ import annotations

from typing import Any

from .github_client import GitHubAPIError


def target_for_event(
    event: dict[str, Any],
    *,
    tracker_repository: str,
    tracker_issue_number: int | None,
) -> tuple[str, int] | None:
    """Choose the source Issue for task/PR events or the central tracker."""
    kind = event.get("kind")
    if kind in {"task_done", "task_reopened"} and event.get("repository") and event.get("number"):
        return str(event["repository"]), int(event["number"])
    if kind == "pr_merged" and event.get("target_repository") and event.get("target_issue_number"):
        return str(event["target_repository"]), int(event["target_issue_number"])
    if tracker_issue_number:
        return tracker_repository, int(tracker_issue_number)
    return None


def publish_and_verify(client: Any, repository: str, issue_number: int, body: str) -> dict[str, Any]:
    """Create a comment, then read it back from the exact Issue."""
    created = client.create_comment(repository, issue_number, body)
    comment_id = created.get("id")
    if not comment_id:
        raise GitHubAPIError("created comment has no id")
    comments = client.list_comments(repository, issue_number)
    for comment in comments:
        if comment.get("id") == comment_id and comment.get("body") == body:
            return {"id": comment_id, "url": comment.get("html_url") or comment.get("url"), "verified": True}
    raise GitHubAPIError("created comment could not be verified")


def find_state_comment(client: Any, repository: str, issue_number: int) -> tuple[dict[str, Any] | None, dict[str, Any] | None]:
    """Find the latest machine state comment on the central tracker Issue."""
    from .deduplication import decode_state

    comments = client.list_comments(repository, issue_number)
    for comment in reversed(comments):
        state = decode_state(str(comment.get("body") or ""))
        if state is not None:
            return state, comment
    return None, None


def save_state_and_verify(
    client: Any,
    repository: str,
    issue_number: int,
    state: dict[str, Any],
    existing_comment: dict[str, Any] | None,
) -> dict[str, Any]:
    """Create/update the state comment and verify its exact body."""
    from .deduplication import decode_state, encode_state

    body = encode_state(state)
    if existing_comment:
        result = client.update_comment(repository, int(existing_comment["id"]), body)
        comment_id = result.get("id")
    else:
        result = client.create_comment(repository, issue_number, body)
        comment_id = result.get("id")
    if not comment_id:
        raise GitHubAPIError("state comment write returned no id")
    comments = client.list_comments(repository, issue_number)
    for comment in comments:
        if comment.get("id") == comment_id and decode_state(str(comment.get("body") or "")) == state:
            return {"id": comment_id, "verified": True}
    raise GitHubAPIError("state comment could not be verified")
