from __future__ import annotations

from collections import Counter
from datetime import date, datetime

from .collector import Entry
from .llm import Summary


def _dia(iso: str) -> str:
    try:
        return datetime.fromisoformat(iso.replace("Z", "+00:00")).strftime("%d/%m")
    except ValueError:
        return iso[:10]


def facts(entries: list[Entry]) -> list[str]:
    """Uma linha por commit: é tudo o que a IA recebe."""
    linhas = []
    for e in entries:
        pr = f"PR #{e.pull[0]}" if e.pull else "-"
        linhas.append(f"{_dia(e.date)} | {e.frente} | {e.author} | {e.type} | {e.message} | {', '.join(e.issues) or '-'} | {pr}")
    return linhas


def plain_summary(entries: list[Entry]) -> str:
    """Resumo sem IA, montado só dos dados: usado quando nenhum provedor responde."""
    if not entries:
        return "Nenhum commit no período."
    pessoas = Counter(e.author for e in entries)
    frentes = Counter(e.frente for e in entries)
    issues = sorted({i for e in entries for i in e.issues}, key=lambda i: (i.split("#")[0], int(i.split("#")[1])))
    partes = [
        f"{len(entries)} commits de {len(pessoas)} pessoa(s): "
        + ", ".join(f"{p} ({n})" for p, n in pessoas.most_common()) + ".",
        "Frentes: " + ", ".join(f"{f} ({n})" for f, n in frentes.most_common()) + ".",
    ]
    if issues:
        partes.append("Issues citadas: " + ", ".join(i.replace("conloq/mash", "") for i in issues) + ".")
    return " ".join(partes)


def render_week(entries: list[Entry], since: date, until: date, summary: Summary, failures: list[str]) -> str:
    out = [f"# Diário de Bordo: {since:%d/%m} a {until:%d/%m/%Y}", ""]
    out += ["## Resumo do período", ""]
    if summary.text:
        out += [summary.text, "", f"> Resumo redigido por IA ({summary.provider}) a partir dos commits da tabela abaixo. Revisar antes de aprovar o Pull Request.", ""]
    else:
        out += [plain_summary(entries), "", "> Resumo gerado sem IA, só a partir dos dados.", ""]

    out += ["## Números", ""]
    pessoas = Counter(e.author for e in entries)
    frentes = Counter(e.frente for e in entries)
    out += ["| Pessoa | Commits | Linhas + | Linhas - |", "|---|---|---|---|"]
    for p, n in pessoas.most_common():
        mais = sum(e.additions for e in entries if e.author == p)
        menos = sum(e.deletions for e in entries if e.author == p)
        out.append(f"| {p} | {n} | {mais} | {menos} |")
    out += ["", "| Frente | Commits |", "|---|---|"] + [f"| {f} | {n} |" for f, n in frentes.most_common()] + [""]

    out += ["## Commits", "", "| Data | Frente | Responsável | Tipo | Mensagem | Arquivos | Issues | PR |", "|---|---|---|---|---|---|---|---|"]
    for e in entries:
        msg = e.message.replace("|", "/")
        issues = ", ".join(i.replace("conloq/mash", "") for i in e.issues) or "-"
        pr = f"{e.repository}#{e.pull[0]}" if e.pull else "-"
        out.append(f"| {_dia(e.date)} | {e.frente} | {e.author} | {e.type} | {msg} | {e.files} (+{e.additions}/-{e.deletions}) | {issues} | {pr} |")
    if failures:
        out += ["", "## Repositórios não lidos", ""] + [f"- {f}" for f in failures]
    return "\n".join(out) + "\n"
