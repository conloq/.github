from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from urllib.parse import quote

from automation.mash_project_notifier.github_client import GitHubAPIError

from . import classifier, config


@dataclass(frozen=True)
class Entry:
    repository: str
    sha: str
    date: str  # ISO 8601 do autor do commit
    author: str  # login do GitHub, ou o nome do autor se o commit não estiver ligado a uma conta
    message: str  # primeira linha, sem segredo nem e-mail
    type: str
    frente: str
    issues: tuple[str, ...]
    files: int = 0
    additions: int = 0
    deletions: int = 0
    pull: tuple[int, str] | None = None  # número e título do PR que levou o commit à main


@dataclass
class Collection:
    entries: list[Entry] = field(default_factory=list)
    failures: list[str] = field(default_factory=list)  # repositórios que não puderam ser lidos


def _iso(moment: datetime) -> str:
    return moment.strftime("%Y-%m-%dT%H:%M:%SZ")


def read_commits(client, repositories, since: datetime, until: datetime, *, max_pages: int = 10, aliases: dict[str, str] | None = None) -> Collection:
    """Lê os commits do período (since e until em UTC) na branch padrão de cada repositório.

    Commits de merge e de robôs ([bot]) ficam de fora: o trabalho aparece pelos commits do PR, que trazem o PR ligado.
    O nome do autor de commit sem conta ligada vira o login pelo mapa de apelidos.
    Um repositório que falha não interrompe os outros; a falha é registrada.
    """
    result = Collection()
    for repo in repositories:
        try:
            for page in range(1, max_pages + 1):
                path = f"/repos/{repo}/commits?since={quote(_iso(since))}&until={quote(_iso(until))}&per_page=100&page={page}"
                commits = client.rest("GET", path) or []
                for item in commits:
                    entry = _entry(client, repo, item, aliases or {})
                    if entry:
                        result.entries.append(entry)
                if len(commits) < 100:
                    break
        except GitHubAPIError as exc:
            result.failures.append(f"{repo}: {exc}")
    result.entries.sort(key=lambda e: (e.date, e.repository))
    return result


def _entry(client, repo: str, item: dict, aliases: dict[str, str]) -> Entry | None:
    commit = item.get("commit") or {}
    message = commit.get("message") or ""
    if classifier.is_merge(message, len(item.get("parents") or [])) or message.startswith(config.COMMIT_PREFIX):
        return None
    login = (item.get("author") or {}).get("login")
    if login and login.endswith("[bot]"):
        return None
    sha = item.get("sha") or ""
    name = (commit.get("author") or {}).get("name") or "desconhecido"
    author = login or aliases.get(name.strip().lower(), name)
    detail = client.rest("GET", f"/repos/{repo}/commits/{sha}") or {}
    stats = detail.get("stats") or {}
    pulls = client.rest("GET", f"/repos/{repo}/commits/{sha}/pulls") or []
    pull = (pulls[0]["number"], classifier.sanitize(pulls[0].get("title") or "")) if pulls else None
    return Entry(
        repository=repo,
        sha=sha,
        date=(commit.get("author") or {}).get("date") or "",
        author=classifier.sanitize(author),
        message=classifier.first_line(message),
        type=classifier.commit_type(message),
        frente=classifier.frente(repo),
        issues=tuple(classifier.issue_refs(message)),
        files=len(detail.get("files") or []),
        additions=int(stats.get("additions") or 0),
        deletions=int(stats.get("deletions") or 0),
        pull=pull,
    )
