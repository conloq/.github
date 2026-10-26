"""Sprints do Project Mash: o período oficial de cada Diário de Bordo.

As datas vêm só do campo de iteração `Sprint` do Project V2 (conloq #2). Nada aqui
infere duração a partir da issue ou do calendário: sem configuração legível, a
execução falha em vez de publicar um intervalo inventado.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from . import config

PROJECT_QUERY = """
query($organization: String!, $number: Int!) {
  organization(login: $organization) {
    projectV2(number: $number) {
      fields(first: 50) {
        nodes {
          ... on ProjectV2IterationField {
            name
            configuration {
              iterations { title startDate duration }
              completedIterations { title startDate duration }
            }
          }
        }
      }
    }
  }
}
"""


@dataclass(frozen=True)
class Sprint:
    title: str
    start_date: date
    duration: int

    @property
    def last_day(self) -> date:
        """Último dia do período, inclusive."""
        return self.start_date + timedelta(days=self.duration - 1)


def today_local(tz: str = config.LOCAL_TIMEZONE) -> date:
    return datetime.now(ZoneInfo(tz)).date()


def fetch_sprints(client, organization: str = config.PROJECT_ORGANIZATION, number: int = config.PROJECT_NUMBER) -> list[Sprint]:
    return parse_iterations(client.graphql(PROJECT_QUERY, {"organization": organization, "number": number}))


def parse_iterations(payload: dict) -> list[Sprint]:
    """Lê `iterations` e `completedIterations` do campo Sprint, deduplicadas pelo início e em ordem cronológica."""
    try:
        project = payload["data"]["organization"]["projectV2"]
    except (KeyError, TypeError):
        raise config.ConfigurationError("Project Mash (conloq #2) não encontrado na resposta do GraphQL") from None
    fields = [node for node in ((project.get("fields") or {}).get("nodes") or []) if isinstance(node, dict) and node.get("name") == "Sprint"]
    if len(fields) != 1:
        raise config.ConfigurationError(f"Project Mash: esperado exatamente um campo Sprint, encontrado {len(fields)}")
    configuration = fields[0].get("configuration")
    if not isinstance(configuration, dict):
        raise config.ConfigurationError("Project Mash: campo Sprint sem configuração de iterações legível")

    known: dict[date, Sprint] = {}
    for key in ("iterations", "completedIterations"):
        items = configuration.get(key) or []
        if not isinstance(items, list):
            raise config.ConfigurationError(f"Project Mash: {key} do campo Sprint inválido")
        for item in items:
            sprint = _sprint(item)
            known.setdefault(sprint.start_date, sprint)
    return sorted(known.values(), key=lambda sprint: sprint.start_date)


def eligible(sprints: list[Sprint], today: date) -> list[Sprint]:
    """Sprints encerradas antes de hoje: o primeiro dia elegível é o seguinte ao último dia."""
    return [sprint for sprint in sorted(sprints, key=lambda sprint: sprint.start_date) if today > sprint.last_day]


def _sprint(item) -> Sprint:
    title = str(item.get("title") or "") if isinstance(item, dict) else ""
    raw_start = item.get("startDate") if isinstance(item, dict) else None
    duration = item.get("duration") if isinstance(item, dict) else None
    try:
        start = date.fromisoformat(str(raw_start))
    except ValueError:
        raise config.ConfigurationError(f"Project Mash: sprint {title or 'sem título'} sem data de início válida") from None
    if not isinstance(duration, int) or isinstance(duration, bool) or duration < 1:
        raise config.ConfigurationError(f"Project Mash: sprint {title or start.isoformat()} com duração inválida")
    return Sprint(title or start.isoformat(), start, duration)
