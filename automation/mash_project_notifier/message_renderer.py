from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from .deduplication import event_marker

TEAM_MENTION = "@conloq/mash"


def _safe_text(value: Any) -> str:
    """Prevent arbitrary source text from creating extra GitHub mentions."""
    return str(value or "").replace("@", "@\u200b").replace("\r", " ").replace("\n", " ").strip()


def _date_text(value: Any) -> str:
    text = _safe_text(value)
    try:
        from datetime import date

        return date.fromisoformat(text).strftime("%d/%m/%Y")
    except ValueError:
        return text


def _status_counts(values: Mapping[str, int]) -> str:
    return ", ".join(f"{_safe_text(name)} {count}" for name, count in sorted(values.items())) or "(nenhuma)"


def _with_marker(lines: list[str], event: dict[str, Any]) -> str:
    key = event.get("event_key")
    if key:
        lines.extend(["", event_marker(str(key))])
    return "\n".join(lines)


def render_task_event(event: dict[str, Any]) -> str:
    kind = event.get("kind")
    if kind == "task_done":
        heading = "✅ Tarefa concluída"
    elif kind == "task_reopened":
        heading = "↩️ Tarefa reaberta"
    else:
        heading = "ℹ️ Alteração de tarefa"
    number = event.get("number")
    title = _safe_text(event.get("title"))
    issue = f"[#{number} — {title}]({event['url']})" if number and event.get("url") else f"#{number} — {title}"
    return _with_marker(
        [
            TEAM_MENTION,
            "",
            heading,
            "",
            f"- Issue: {issue}",
            f"- Sprint: {_safe_text(event.get('sprint'))}",
            f"- Repositório: `{_safe_text(event.get('repository'))}`",
            f"- Status anterior: {_safe_text(event.get('old_status_name'))}",
            f"- Status atual: {_safe_text(event.get('status_name'))}",
        ],
        event,
    )


def render_daily_summary(
    metrics: dict[str, Any],
    current: dict[str, Any],
    next_sprint: dict[str, Any] | None,
    date_label: str,
) -> str:
    next_line = "- Próxima Sprint: não encontrada"
    if next_sprint:
        next_line = "\n".join(
            [
                f"- Próxima Sprint: {_safe_text(next_sprint.get('title'))}",
                f"- Início da próxima Sprint: {_date_text(next_sprint.get('startDate'))}",
                f"- Faltam: {next_sprint.get('days_until_start')} dias corridos",
            ]
        )
    return "\n".join(
        [
            TEAM_MENTION,
            "",
            f"📊 Acompanhamento do Projeto Mash — {date_label}",
            "",
            f"Sprint atual: {_safe_text(metrics.get('sprint'))}",
            f"Período: {_date_text(current.get('startDate'))}–{_date_text(current.get('endDate'))}",
            "",
            f"- Tarefas totais: {metrics.get('total', 0)}",
            f"- Concluídas: {metrics.get('done', 0)}",
            f"- Restantes: {metrics.get('remaining', 0)}",
            f"- Por status: {_status_counts(metrics.get('status_counts', {}))}",
            next_line,
            "",
            "Observação: o relatório informa o estado observado e não estima a data de conclusão.",
        ]
    )


def render_calendar_event(event: dict[str, Any]) -> str:
    kind = event.get("kind")
    sprint = _safe_text(event.get("sprint") or event.get("target"))
    if kind == "sprint_started":
        heading = "🚀 Nova Sprint iniciada"
        detail = f"A {sprint} começou hoje."
    elif kind == "next_sprint_threshold":
        heading = "⏳ Próxima Sprint se aproximando"
        detail = f"A {sprint} começa em {event.get('days')} dias corridos."
    elif kind == "sprint_deadline":
        heading = "⚠️ Sprint terminando com pendências"
        metrics = event.get("metrics") or {}
        detail = f"A {sprint} termina em {event.get('days')} dias corridos e ainda possui {metrics.get('remaining', 0)} tarefa(s) restante(s)."
    elif kind == "sprint_completed":
        heading = "✅ Sprint concluída"
        detail = f"Todas as tarefas da {sprint} estão em Done."
    else:
        heading = "ℹ️ Atualização de Sprint"
        detail = f"Atualização da {sprint}."
    lines = [
        TEAM_MENTION,
        "",
        heading,
        "",
        detail,
        f"- Data de referência: {_date_text(event.get('date'))}",
    ]
    return _with_marker(lines, event)


def render_pr_event(event: dict[str, Any]) -> str:
    title = _safe_text(event.get("title"))
    pr = f"[#{event.get('number')} — {title}]({event.get('url')})" if event.get("url") else f"#{event.get('number')} — {title}"
    linked = _safe_text(event.get("linked_issue")) or "não identificada"
    return _with_marker(
        [
            TEAM_MENTION,
            "",
            "🔀 Pull Request mesclada",
            "",
            f"- PR: {pr}",
            f"- Repositório: `{_safe_text(event.get('repository'))}`",
            f"- Issue relacionada: {linked}",
            "- Esta evidência não aumenta a contagem de tarefas do Project.",
        ],
        event,
    )
