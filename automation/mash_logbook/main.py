"""Diário de Bordo do Mash a partir dos commits dos repositórios.

Uso local (só gera o arquivo, não publica nada):
    python -m automation.mash_logbook.main --since 2026-10-08 --until 2026-10-14 --output diario.md

Com --publish, também abre o Pull Request do diário no repositório de documentação.

Sem --since/--until, usa a semana anterior (segunda a domingo, horário de São Paulo).
Com --sprint, usa as datas do campo Sprint do Project Mash e processa só as sprints
encerradas cujo diário ainda não está publicado.
O resumo é redigido por IA quando algum provedor responde; senão, sai montado só dos dados.
"""
from __future__ import annotations

import argparse
import os
import sys
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from automation.mash_project_notifier.github_client import GitHubAPIError, GitHubClient

from . import config, llm, publisher, renderer, sprints
from .collector import read_commits


def previous_week(today: date) -> tuple[date, date]:
    start = today - timedelta(days=today.weekday() + 7)
    return start, start + timedelta(days=6)


def utc_range(since: date, until: date, tz: str = config.LOCAL_TIMEZONE) -> tuple[datetime, datetime]:
    zone = ZoneInfo(tz)
    start = datetime.combine(since, time.min, zone).astimezone(timezone.utc)
    end = datetime.combine(until, time.max, zone).astimezone(timezone.utc)
    return start, end


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Gera o Diário de Bordo do Mash.")
    parser.add_argument("--since", type=date.fromisoformat, help="primeiro dia (AAAA-MM-DD)")
    parser.add_argument("--until", type=date.fromisoformat, help="último dia, inclusive (AAAA-MM-DD)")
    parser.add_argument("--sprint", action="store_true", help="processa as sprints encerradas ainda não publicadas (Project Mash)")
    parser.add_argument("--output", help="arquivo Markdown de saída; sem ele, imprime no terminal")
    parser.add_argument("--no-ai", action="store_true", help="não chama nenhum provedor de IA")
    parser.add_argument(
        "--publish", action="store_true", help=f"abre o Pull Request do diário em {config.LOGBOOK_REPOSITORY}"
    )
    args = parser.parse_args(argv)
    if args.sprint and (args.since or args.until):
        parser.error("--sprint não combina com --since/--until")
    if args.sprint and args.output:
        parser.error("--output não se aplica a --sprint: cada sprint vira um arquivo próprio no repositório")
    return args


def generate(client, env: dict[str, str], since: date, until: date, *, no_ai: bool = False, opener=None):
    start, end = utc_range(since, until)
    collected = read_commits(client, config.REPOSITORIES, start, end, aliases=config.load_aliases(env))

    entries = collected.entries
    if no_ai or not entries:
        summary = llm.Summary(None, None, [])
    else:
        prompt = llm.build_prompt(f"{since:%d/%m} a {until:%d/%m/%Y}", renderer.facts(entries))
        numeros = {i.split("#")[1] for e in entries for i in e.issues} | {str(e.pull[0]) for e in entries if e.pull}
        summary = llm.summarize(config.load_providers(env), env, prompt, numeros, {e.author for e in entries}, opener=opener)

    return renderer.render_week(entries, since, until, summary, collected.failures), collected, summary


def report(collected, summary, no_ai: bool) -> None:
    """Relatório para quem roda: nunca mostra chave nem resposta de erro do provedor."""
    print(f"\n{len(collected.entries)} commits em {len(config.REPOSITORIES) - len(collected.failures)} repositórios.", file=sys.stderr)
    for a in summary.attempts:
        print(f"  IA {a.provider}: {'usada' if a.ok else a.reason}", file=sys.stderr)
    if not summary.text:
        print("  resumo sem IA" + (" (--no-ai)" if no_ai else ""), file=sys.stderr)
    for f in collected.failures:
        print(f"  não lido: {f}", file=sys.stderr)


def run_sprints(args: argparse.Namespace, env: dict[str, str], client, opener, today: date) -> int:
    """Publica um PR por sprint encerrada cujo arquivo ainda não está no branch padrão, em ordem cronológica."""
    known = sprints.fetch_sprints(client)
    pending = [sprint for sprint in sprints.eligible(known, today) if not publisher.is_published(client, sprint.start_date)]
    if not pending:
        print(f"Nenhuma sprint encerrada pendente em {today:%d/%m/%Y}.", file=sys.stderr)
        return 0

    for sprint in pending:
        markdown, collected, summary = generate(
            client, env, sprint.start_date, sprint.last_day, no_ai=args.no_ai, opener=opener
        )
        sys.stdout.write(markdown)
        if args.publish:
            url = publisher.publish(client, markdown, sprint.start_date, sprint.last_day)
            print(f"Pull Request de {sprint.title}: {url}", file=sys.stderr)
        report(collected, summary, args.no_ai)
    return 0


def run(argv: list[str] | None = None, env: dict[str, str] | None = None, client=None, opener=None, today: date | None = None) -> int:
    env = dict(os.environ) if env is None else env
    args = parse_args(argv)
    client = client or GitHubClient(config.github_token(env))
    if args.sprint:
        return run_sprints(args, env, client, opener, today or sprints.today_local())

    since, until = (args.since, args.until) if args.since and args.until else previous_week(datetime.now(ZoneInfo(config.LOCAL_TIMEZONE)).date())
    if since > until:
        print("--since depois de --until", file=sys.stderr)
        return 2
    markdown, collected, summary = generate(client, env, since, until, no_ai=args.no_ai, opener=opener)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as fh:
            fh.write(markdown)
    else:
        sys.stdout.write(markdown)
    if args.publish:
        print(f"Pull Request do diário: {publisher.publish(client, markdown, since, until)}", file=sys.stderr)
    report(collected, summary, args.no_ai)
    return 0


def main() -> None:
    try:
        sys.exit(run())
    except config.ConfigurationError as exc:
        print(f"configuração: {exc}", file=sys.stderr)
        sys.exit(2)
    except GitHubAPIError as exc:
        print(f"github: {exc}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
