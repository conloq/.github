from datetime import datetime, timezone

from automation.mash_logbook.collector import read_commits
from automation.mash_project_notifier.github_client import GitHubAPIError


class FakeClient:
    def __init__(self, commits_by_repo, failing=()):
        self.commits_by_repo = commits_by_repo
        self.failing = set(failing)
        self.paths = []

    def rest(self, method, path):
        self.paths.append(path)
        repo = "/".join(path.split("/")[2:4])
        if repo in self.failing:
            raise GitHubAPIError("GitHub API returned HTTP 409")
        if path.endswith("/pulls"):
            return [{"number": 8, "title": "feat: liberar CORS"}]
        if "/commits/" in path:
            return {"stats": {"additions": 10, "deletions": 2}, "files": [{}, {}]}
        return self.commits_by_repo.get(repo, [])


def commit(sha, message, login="haimonvieira", parents=1, when="2026-10-13T12:00:00Z"):
    return {"sha": sha, "parents": [{}] * parents, "author": {"login": login}, "commit": {"message": message, "author": {"date": when, "name": "Haimon"}}}


def test_read_commits_skips_merges_attaches_pr_and_records_failures():
    client = FakeClient(
        {
            "conloq/Back-End": [commit("a1", "feat: liberar CORS (#66)"), commit("m1", "Merge pull request #8 from x", parents=2)],
            "conloq/frontend": [commit("b1", "fix: login\n\ncorpo com joao@exemplo.com", login=None, when="2026-10-12T10:00:00Z")],
        },
        failing=["conloq/database"],
    )
    since = datetime(2026, 10, 8, tzinfo=timezone.utc)
    until = datetime(2026, 10, 15, tzinfo=timezone.utc)
    result = read_commits(client, ["conloq/Back-End", "conloq/frontend", "conloq/database"], since, until)

    assert [e.sha for e in result.entries] == ["b1", "a1"]  # ordenado por data
    backend = result.entries[1]
    assert backend.frente == "Backend" and backend.type == "Funcionalidade"
    assert backend.issues == ("conloq/mash#66",)
    assert backend.pull == (8, "feat: liberar CORS")
    assert (backend.files, backend.additions, backend.deletions) == (2, 10, 2)
    assert result.entries[0].author == "Haimon"  # sem conta ligada, usa o nome do autor
    assert "@" not in result.entries[0].message
    assert result.failures == ["conloq/database: GitHub API returned HTTP 409"]
    assert any("since=2026-10-08T00%3A00%3A00Z" in p for p in client.paths)


def test_aliases_map_unlinked_names_and_bots_are_skipped():
    client = FakeClient({"conloq/Back-End": [commit("c1", "docs: x", login=None), commit("c2", "fix: y", login="coderabbitai[bot]")]})
    since = datetime(2026, 10, 8, tzinfo=timezone.utc)
    result = read_commits(client, ["conloq/Back-End"], since, since, aliases={"haimon": "haimonvieira"})
    assert [(e.sha, e.author) for e in result.entries] == [("c1", "haimonvieira")]


def test_logbook_own_commits_are_skipped():
    client = FakeClient({"conloq/documentation": [commit("d1", "docs(diario-de-bordo): 05/10 a 11/10/2026"), commit("d2", "docs: guia")]})
    since = datetime(2026, 10, 8, tzinfo=timezone.utc)
    result = read_commits(client, ["conloq/documentation"], since, since)
    assert [e.sha for e in result.entries] == ["d2"]
