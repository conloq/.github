from datetime import date

import pytest

from automation.mash_logbook import main, renderer
from automation.mash_logbook.collector import Entry
from automation.mash_logbook.llm import Summary
from automation.mash_project_notifier.github_client import GitHubAPIError

ENTRY = Entry("conloq/Back-End", "a1", "2026-10-13T12:00:00Z", "haimonvieira", "feat: CORS (#66)", "Funcionalidade", "Backend", ("conloq/mash#66",), 2, 10, 2, (8, "CORS"))


def test_render_without_ai_uses_plain_summary_and_marks_it():
    md = renderer.render_week([ENTRY], date(2026, 10, 8), date(2026, 10, 14), Summary(None, None, []), [])
    assert md.startswith("# Diário de Bordo: 08/10 a 14/10/2026")
    assert "1 commits de 1 pessoa(s): haimonvieira (1)." in md
    assert "Resumo gerado sem IA" in md
    assert "| 13/10 | Backend | haimonvieira | Funcionalidade | feat: CORS (#66) | 2 (+10/-2) | #66 | conloq/Back-End#8 |" in md


def test_render_with_ai_names_the_provider_and_asks_for_review():
    md = renderer.render_week([ENTRY], date(2026, 10, 8), date(2026, 10, 14), Summary("Texto da IA.", "groq", []), ["conloq/database: HTTP 409"])
    assert "Texto da IA." in md and "redigido por IA (groq)" in md
    assert "## Repositórios não lidos" in md


def test_previous_week_is_monday_to_sunday():
    assert main.previous_week(date(2026, 10, 15)) == (date(2026, 10, 5), date(2026, 10, 11))
    assert main.previous_week(date(2026, 10, 19)) == (date(2026, 10, 12), date(2026, 10, 18))


def test_utc_range_covers_whole_days_in_sao_paulo():
    start, end = main.utc_range(date(2026, 10, 8), date(2026, 10, 14))
    assert start.isoformat() == "2026-10-08T03:00:00+00:00"
    assert end.isoformat().startswith("2026-10-15T02:59:59")


class EmptyClient:
    def rest(self, method, path):
        return []


def test_run_writes_file_without_calling_ai_when_no_commits(tmp_path, capsys):
    out = tmp_path / "diario.md"
    code = main.run(["--since", "2026-10-08", "--until", "2026-10-14", "--output", str(out)], env={}, client=EmptyClient())
    assert code == 0
    assert "Nenhum commit no período." in out.read_text(encoding="utf-8")
    assert "0 commits" in capsys.readouterr().err


def iteration(title, start, duration):
    return {"title": title, "startDate": start, "duration": duration}


class SprintClient:
    """Cliente falso do Project e do logbook: nenhum commit e nenhum arquivo publicado por padrão."""

    def __init__(self, iterations=(), completed=(), published=()):
        self.iterations, self.completed, self.published = list(iterations), list(completed), set(published)
        self.calls = []

    def graphql(self, query, variables=None):
        return {
            "data": {
                "organization": {
                    "projectV2": {
                        "fields": {
                            "nodes": [
                                {"name": "Status"},
                                {
                                    "name": "Sprint",
                                    "configuration": {"iterations": self.iterations, "completedIterations": self.completed},
                                },
                            ]
                        }
                    }
                }
            }
        }

    def rest(self, method, path, payload=None):
        self.calls.append((method, path))
        if method == "GET" and "/commits" in path:
            return []
        if (method, path) == ("GET", "/repos/conloq/logbook-backup"):
            return {"default_branch": "main"}
        if method == "GET" and "/contents/" in path:
            start = path.split("diario-de-bordo/")[1].split(".md")[0]
            if start in self.published:
                return {"sha": "publicado"}
            raise GitHubAPIError("GitHub API returned HTTP 404")
        raise AssertionError(f"chamada inesperada: {method} {path}")


def record_publish(monkeypatch):
    calls = []
    monkeypatch.setattr(main.publisher, "publish", lambda client, markdown, since, until: calls.append((since, until)) or "https://x/pull/1")
    return calls


def test_sprint_mode_does_not_publish_a_sprint_that_ends_today(monkeypatch):
    calls = record_publish(monkeypatch)
    client = SprintClient(iterations=[iteration("Sprint 5", "2026-10-16", 15)])
    assert main.run(["--sprint", "--publish", "--no-ai"], env={}, client=client, today=date(2026, 10, 30)) == 0
    assert calls == []


def test_sprint_mode_publishes_the_day_after_with_the_inclusive_range(monkeypatch, capsys):
    calls = record_publish(monkeypatch)
    client = SprintClient(iterations=[iteration("Sprint 5", "2026-10-16", 15)])
    assert main.run(["--sprint", "--publish", "--no-ai"], env={}, client=client, today=date(2026, 10, 31)) == 0
    assert calls == [(date(2026, 10, 16), date(2026, 10, 30))]
    assert "# Diário de Bordo: 16/10 a 30/10/2026" in capsys.readouterr().out


def test_sprint_mode_skips_a_diary_already_on_the_default_branch(monkeypatch):
    calls = record_publish(monkeypatch)
    client = SprintClient(iterations=[iteration("Sprint 5", "2026-10-16", 15)], published=["2026-10-16"])
    assert main.run(["--sprint", "--publish", "--no-ai"], env={}, client=client, today=date(2026, 10, 31)) == 0
    assert calls == []
    assert ("GET", "/repos/conloq/logbook-backup/contents/diario-de-bordo/2026-10-16.md?ref=main") in client.calls


def test_sprint_mode_publishes_every_pending_sprint_in_chronological_order(monkeypatch):
    calls = record_publish(monkeypatch)
    client = SprintClient(
        iterations=[iteration("Sprint 5", "2026-10-16", 15)],
        completed=[iteration("Sprint 4", "2026-10-01", 15)],
    )
    assert main.run(["--sprint", "--publish", "--no-ai"], env={}, client=client, today=date(2026, 10, 31)) == 0
    assert calls == [(date(2026, 10, 1), date(2026, 10, 15)), (date(2026, 10, 16), date(2026, 10, 30))]


def test_sprint_mode_stops_when_the_project_cannot_be_read(monkeypatch):
    calls = record_publish(monkeypatch)

    class BrokenClient(SprintClient):
        def graphql(self, query, variables=None):
            raise GitHubAPIError("GitHub GraphQL error: forbidden")

    with pytest.raises(GitHubAPIError):
        main.run(["--sprint", "--publish", "--no-ai"], env={}, client=BrokenClient(), today=date(2026, 10, 31))
    assert calls == []


def test_sprint_mode_rejects_explicit_dates():
    with pytest.raises(SystemExit):
        main.parse_args(["--sprint", "--since", "2026-10-01", "--until", "2026-10-15"])
