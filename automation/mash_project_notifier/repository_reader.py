from __future__ import annotations

import re
from datetime import datetime, timezone
from typing import Any, Iterable


_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?Z")
_URL_ISSUE_RE = re.compile(r"https://github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+)/issues/(\d+)")
_QUALIFIED_RE = re.compile(r"\b([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)#(\d+)\b")
_LOCAL_RE = re.compile(r"(?<![\w/])#(\d+)\b")


def _parse_timestamp(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)


def read_pull_requests(
    client: Any,
    repositories: Iterable[str],
    since: str | None = None,
) -> list[dict[str, Any]]:
    """Read recently updated PRs from an explicit repository allowlist."""
    threshold = _parse_timestamp(since) if since else None
    result: list[dict[str, Any]] = []
    for repository in repositories:
        path = f"/repos/{repository}/pulls?state=all&sort=updated&direction=desc&per_page=100"
        payload = client.rest("GET", path)
        if not isinstance(payload, list):
            raise ValueError(f"unexpected pull request response for {repository}")
        for raw in payload:
            updated_at = raw.get("updated_at")
            if threshold and updated_at and _parse_timestamp(updated_at) < threshold:
                continue
            result.append(
                {
                    "repository": repository,
                    "number": raw.get("number"),
                    "title": raw.get("title") or "",
                    "body": raw.get("body") or "",
                    "url": raw.get("html_url") or raw.get("url"),
                    "state": raw.get("state"),
                    "merged_at": raw.get("merged_at"),
                    "updated_at": updated_at,
                    "user": (raw.get("user") or {}).get("login"),
                }
            )
    return sorted(result, key=lambda pr: pr.get("updated_at") or "")


def link_pull_request_to_issue(pr: dict[str, Any]) -> list[dict[str, Any]]:
    """Resolve only explicit Issue references from a PR.

    A bare ``#N`` is local to the planning repository only. Cross-repository
    PRs must use ``owner/repo#N`` or a full GitHub Issue URL.
    """
    repository = str(pr.get("repository") or "")
    text = f"{pr.get('title') or ''}\n{pr.get('body') or ''}"
    found: list[dict[str, Any]] = []
    seen: set[tuple[str, int]] = set()

    def add(repo: str, number: str) -> None:
        key = (repo, int(number))
        if key not in seen:
            seen.add(key)
            found.append({"repository": repo, "number": int(number)})

    for owner, repo, number in _URL_ISSUE_RE.findall(text):
        add(f"{owner}/{repo}", number)
    for repo, number in _QUALIFIED_RE.findall(text):
        add(repo, number)
    if repository == "conloq/mash":
        for number in _LOCAL_RE.findall(text):
            add(repository, number)
    return found
