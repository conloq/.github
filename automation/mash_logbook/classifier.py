from __future__ import annotations

import re

from .config import DEFAULT_REPOSITORY, FRENTES

TIPOS = {
    "feat": "Funcionalidade",
    "fix": "Correção",
    "docs": "Documentação",
    "chore": "Manutenção",
    "test": "Testes",
    "refactor": "Refatoração",
    "style": "Estilo",
    "ci": "Integração contínua",
    "build": "Build",
    "perf": "Desempenho",
}
_PREFIXO = re.compile(r"^(\w+)(?:\([^)]*\))?!?:", re.I)
_MERGE = re.compile(r"^Merge pull request #\d+", re.I)
_REF = re.compile(r"(?<![\w/])(?:([\w.-]+/[\w.-]+))?#(\d+)\b")

# Segredos e dados pessoais nunca vão para o texto nem para a IA.
_SEGREDO = re.compile(
    r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|gh[ousr]_[A-Za-z0-9]{20,}|sk-[A-Za-z0-9_-]{16,}"
    r"|AKIA[0-9A-Z]{16}|[\w.+-]+@[\w-]+\.[\w.-]+)"
)


def frente(repository: str) -> str:
    return FRENTES.get(repository, "Outra")


def commit_type(message: str) -> str:
    m = _PREFIXO.match(message.strip())
    return TIPOS.get(m.group(1).lower(), "Outro") if m else "Outro"


def issue_refs(message: str) -> list[str]:
    """Referências a issues. `#N` sem repositório é conloq/mash#N, onde ficam as issues do projeto.

    O número do PR em "Merge pull request #N" não é issue e fica de fora.
    """
    texto = _MERGE.sub("", message)
    refs = []
    for repo, numero in _REF.findall(texto):
        ref = f"{repo or DEFAULT_REPOSITORY}#{numero}"
        if ref not in refs:
            refs.append(ref)
    return refs


def sanitize(text: str) -> str:
    return _SEGREDO.sub("[removido]", text)


def first_line(message: str) -> str:
    return sanitize(message.strip().splitlines()[0] if message.strip() else "")


def is_merge(message: str, parents: int) -> bool:
    return parents > 1 or bool(_MERGE.match(message.strip()))
