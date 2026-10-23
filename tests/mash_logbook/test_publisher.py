import base64
from datetime import date

import pytest

from automation.mash_logbook import publisher
from automation.mash_project_notifier.github_client import GitHubAPIError

REPO = "/repos/conloq/documentation"


class FakeClient:
    def __init__(self, branch_exists=False, file_sha=None, open_pulls=(), ref_error="HTTP 404"):
        self.branch_exists, self.file_sha, self.open_pulls, self.ref_error = branch_exists, file_sha, list(open_pulls), ref_error
        self.calls = []

    def rest(self, method, path, payload=None):
        self.calls.append((method, path, payload))
        if (method, path) == ("GET", REPO):
            return {"default_branch": "main"}
        if method == "GET" and "/git/ref/heads/diario-de-bordo/" in path:
            if self.branch_exists:
                return {"object": {"sha": "b"}}
            raise GitHubAPIError(f"GitHub API returned {self.ref_error}")
        if method == "GET" and path.endswith("/git/ref/heads/main"):
            return {"object": {"sha": "base-sha"}}
        if method == "GET" and "/contents/" in path:
            if self.file_sha:
                return {"sha": self.file_sha}
            raise GitHubAPIError("GitHub API returned HTTP 404")
        if method == "GET" and "/pulls?" in path:
            return self.open_pulls
        if method == "POST" and path.endswith("/pulls"):
            return {"html_url": "https://github.com/conloq/documentation/pull/9"}
        return {}


def test_first_run_creates_branch_file_and_pull_request():
    client = FakeClient()
    url = publisher.publish(client, "# Diário\n", date(2026, 10, 12), date(2026, 10, 18))
    assert url.endswith("/pull/9")
    assert ("POST", f"{REPO}/git/refs", {"ref": "refs/heads/diario-de-bordo/2026-10-12", "sha": "base-sha"}) in client.calls
    put = next(p for m, path, p in client.calls if m == "PUT")
    assert put["branch"] == "diario-de-bordo/2026-10-12" and "sha" not in put
    assert put["message"] == "docs(diario-de-bordo): 12/10 a 18/10/2026"
    assert base64.b64decode(put["content"]).decode() == "# Diário\n"
    assert any(m == "PUT" and path == f"{REPO}/contents/geral/diario-de-bordo/2026-10-12.md" for m, path, _ in client.calls)
    pr = next(p for m, path, p in client.calls if m == "POST" and path.endswith("/pulls"))
    assert (pr["head"], pr["base"]) == ("diario-de-bordo/2026-10-12", "main")


def test_rerun_updates_file_and_reuses_open_pull_request():
    client = FakeClient(branch_exists=True, file_sha="old", open_pulls=[{"html_url": "https://x/pull/3"}])
    assert publisher.publish(client, "novo", date(2026, 10, 12), date(2026, 10, 18)) == "https://x/pull/3"
    assert not any(m == "POST" for m, _, _ in client.calls)
    assert next(p for m, _, p in client.calls if m == "PUT")["sha"] == "old"


def test_errors_other_than_not_found_stop_publication():
    with pytest.raises(GitHubAPIError):
        publisher.publish(FakeClient(ref_error="HTTP 403"), "x", date(2026, 10, 12), date(2026, 10, 18))
