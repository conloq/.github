from __future__ import annotations

import json
import os
from dataclasses import dataclass

LOCAL_TIMEZONE = "America/Sao_Paulo"
DEFAULT_REPOSITORY = "conloq/mash"

# Project V2 "Mash" da organização: o campo Sprint define o período de cada diário.
PROJECT_ORGANIZATION = "conloq"
PROJECT_NUMBER = 2

# Todos os repositórios do projeto: o Diário de Bordo cobre código, documentação e planejamento.
REPOSITORIES = (
    "conloq/Back-End",
    "conloq/frontend",
    "conloq/landing-page-conloq",
    "conloq/database",
    "conloq/documentation",
    "conloq/.github",
    "conloq/mash",
)

FRENTES = {
    "conloq/Back-End": "Backend",
    "conloq/frontend": "Frontend",
    "conloq/landing-page-conloq": "Design",
    "conloq/database": "Banco de dados",
    "conloq/documentation": "Documentação",
    "conloq/.github": "Automação",
    "conloq/mash": "Planejamento",
}


# Commit feito sem a conta do GitHub ligada ao e-mail chega só com o nome do autor.
# Chave em minúsculas: nome do autor no git -> login no GitHub. Acrescente outros por LOGBOOK_AUTHOR_ALIASES (JSON).
AUTHOR_ALIASES = {
    "haimon vieira": "haimonvieira",
    "haimon cugler vieira": "haimonvieira",
    "joao": "joaoalexandre77",
    "joão alexandre pinto camargo": "joaoalexandre77",
}


def load_aliases(env: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ if env is None else env
    aliases = dict(AUTHOR_ALIASES)
    raw = env.get("LOGBOOK_AUTHOR_ALIASES", "").strip()
    if raw:
        try:
            aliases.update({str(k).strip().lower(): str(v) for k, v in json.loads(raw).items()})
        except (json.JSONDecodeError, AttributeError) as exc:
            raise ConfigurationError("LOGBOOK_AUTHOR_ALIASES deve ser um objeto JSON nome -> login") from exc
    return aliases


class ConfigurationError(ValueError):
    """Configuração ausente ou inválida."""


@dataclass(frozen=True)
class Provider:
    """Provedor de IA com API compatível com a da OpenAI (`POST {base_url}/chat/completions`)."""

    name: str
    base_url: str
    model: str
    key_env: str


# Ordem de tentativa. Sem a chave no ambiente, o provedor é pulado; se todos falharem,
# o resumo sai sem IA. Modelos gratuitos mudam com frequência: confira o nome do modelo
# no site de cada provedor e, se preciso, troque pela variável LOGBOOK_LLM_PROVIDERS.
DEFAULT_PROVIDERS = (
    Provider("groq", "https://api.groq.com/openai/v1", "openai/gpt-oss-120b", "GROQ_API_KEY"),
    Provider("openrouter", "https://openrouter.ai/api/v1", "google/gemma-4-31b-it:free", "OPENROUTER_API_KEY"),
)

# Onde o diário é publicado, por branch e Pull Request.
LOGBOOK_REPOSITORY = "conloq/logbook-backup"
LOGBOOK_DIR = "diario-de-bordo"
# Prefixo do commit do próprio diário: a coleta das semanas seguintes o ignora.
COMMIT_PREFIX = "docs(diario-de-bordo):"


def load_providers(env: dict[str, str] | None = None) -> list[Provider]:
    """Lê LOGBOOK_LLM_PROVIDERS (lista JSON de {name, base_url, model, key_env}) ou usa a lista padrão."""
    env = os.environ if env is None else env
    raw = env.get("LOGBOOK_LLM_PROVIDERS", "").strip()
    if not raw:
        return list(DEFAULT_PROVIDERS)
    try:
        items = json.loads(raw)
        return [Provider(str(i["name"]), str(i["base_url"]), str(i["model"]), str(i["key_env"])) for i in items]
    except (json.JSONDecodeError, KeyError, TypeError) as exc:
        raise ConfigurationError(
            "LOGBOOK_LLM_PROVIDERS deve ser uma lista JSON de objetos com name, base_url, model e key_env"
        ) from exc


def github_token(env: dict[str, str] | None = None) -> str:
    env = os.environ if env is None else env
    token = env.get("MASH_PROJECT_TOKEN") or env.get("GITHUB_TOKEN") or ""
    if not token:
        raise ConfigurationError("MASH_PROJECT_TOKEN ou GITHUB_TOKEN é obrigatório para ler os commits")
    return token
