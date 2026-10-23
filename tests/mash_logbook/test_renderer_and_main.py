from datetime import date

from automation.mash_logbook import main, renderer
from automation.mash_logbook.collector import Entry
from automation.mash_logbook.llm import Summary

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
