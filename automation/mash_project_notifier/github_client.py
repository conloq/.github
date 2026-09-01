from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any


class GitHubAPIError(RuntimeError):
    """Safe API error that never includes credentials or response bodies."""


class GitHubClient:
    def __init__(
        self,
        token: str,
        *,
        api_url: str = "https://api.github.com",
        opener: Callable[..., Any] | None = None,
        timeout: int = 30,
    ) -> None:
        if not token:
            raise ValueError("token is required")
        self._token = token
        self._api_url = api_url.rstrip("/")
        self._opener = opener or urllib.request.urlopen
        self._timeout = timeout

    def _request(self, method: str, url: str, payload: dict[str, Any] | None = None) -> Any:
        body = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(url, data=body, method=method.upper())
        request.add_header("Accept", "application/vnd.github+json")
        request.add_header("Content-Type", "application/json")
        request.add_header("Authorization", f"Bearer {self._token}")
        request.add_header("User-Agent", "mash-project-notifier/0.1")
        try:
            with self._opener(request, timeout=self._timeout) as response:
                raw = response.read()
        except urllib.error.HTTPError as exc:
            raise GitHubAPIError(f"GitHub API returned HTTP {exc.code}") from None
        except urllib.error.URLError as exc:
            raise GitHubAPIError(f"GitHub API network error: {exc.reason}") from None
        try:
            return json.loads(raw.decode("utf-8")) if raw else None
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise GitHubAPIError("GitHub API returned invalid JSON") from exc

    def graphql(self, query: str, variables: dict[str, Any] | None = None) -> dict[str, Any]:
        payload = self._request("POST", f"{self._api_url}/graphql", {"query": query, "variables": variables or {}})
        if not isinstance(payload, dict):
            raise GitHubAPIError("GitHub GraphQL returned an invalid payload")
        if payload.get("errors"):
            messages = "; ".join(str(item.get("message", "unknown error")) for item in payload["errors"])
            raise GitHubAPIError(f"GitHub GraphQL error: {messages}")
        return payload

    def rest(self, method: str, path: str, payload: dict[str, Any] | None = None) -> Any:
        if not path.startswith("/"):
            path = "/" + path
        return self._request(method, f"{self._api_url}{path}", payload)

    def list_comments(self, repository: str, issue_number: int) -> list[dict[str, Any]]:
        payload = self.rest("GET", f"/repos/{repository}/issues/{issue_number}/comments?per_page=100")
        if not isinstance(payload, list):
            raise GitHubAPIError("GitHub comments response is invalid")
        return payload

    def create_comment(self, repository: str, issue_number: int, body: str) -> dict[str, Any]:
        payload = self.rest("POST", f"/repos/{repository}/issues/{issue_number}/comments", {"body": body})
        if not isinstance(payload, dict) or not payload.get("id"):
            raise GitHubAPIError("GitHub did not return the created comment")
        return payload

    def update_comment(self, repository: str, comment_id: int, body: str) -> dict[str, Any]:
        payload = self.rest("PATCH", f"/repos/{repository}/issues/comments/{comment_id}", {"body": body})
        if not isinstance(payload, dict) or not payload.get("id"):
            raise GitHubAPIError("GitHub did not return the updated comment")
        return payload
