from __future__ import annotations

import json
import re
import socket
import urllib.error
import urllib.request
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from .config import Provider

SYSTEM_PROMPT = (
    "Você escreve o Diário de Bordo de um projeto acadêmico de software. "
    "Use somente os fatos fornecidos. Não invente entrega, issue, número, pessoa, data nem resultado. "
    "Escreva em português do Brasil, com frases curtas e diretas, sem travessão, sem jargão e sem adjetivos de propaganda. "
    "Cite issues apenas no formato #N e somente as que aparecem nos fatos. Não use links."
)

_REF_RESPOSTA = re.compile(r"(?<![\w/])(?:[\w.-]+/[\w.-]+)?#(\d+)\b")
MAX_CHARS = 4000


@dataclass
class Attempt:
    provider: str
    ok: bool
    reason: str


@dataclass
class Summary:
    text: str | None
    provider: str | None
    attempts: list[Attempt] = field(default_factory=list)


def build_prompt(period: str, facts: list[str]) -> str:
    return (
        f"Período: {period}.\n"
        "Fatos do período, um por linha (data | frente | responsável | tipo | mensagem do commit | issues | PR):\n"
        + "\n".join(facts)
        + "\n\nEscreva em Markdown, sem título:\n"
        "1. Um parágrafo de resumo do período, com 3 a 5 frases.\n"
        "2. Uma lista chamada **Por frente**, com no máximo duas frases curtas para cada frente que teve atividade. Junte os commits parecidos; não descreva commit por commit.\n"
        "Se uma frente não aparece nos fatos, não a mencione."
    )


def validate(text: str, allowed_issue_numbers: set[str], authors: set[str]) -> str | None:
    """Motivo da recusa, ou None se a resposta pode ser usada."""
    if not text.strip():
        return "resposta vazia"
    if len(text) > MAX_CHARS:
        return f"resposta com mais de {MAX_CHARS} caracteres"
    if "http://" in text or "https://" in text:
        return "resposta com link"
    inventadas = sorted({n for n in _REF_RESPOSTA.findall(text)} - allowed_issue_numbers)
    if inventadas:
        return "issue que não está nos fatos: " + ", ".join("#" + n for n in inventadas)
    for login in re.findall(r"@([A-Za-z0-9-]+)", text):
        if login not in authors:
            return f"pessoa que não está nos fatos: @{login}"
    return None


def _clean(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = re.sub(r"^```\w*\n?|```$", "", text).strip()
    return re.sub(r"\s*[—–]\s*", ", ", text)  # travessão longo ou curto


def summarize(
    providers: list[Provider],
    env: dict[str, str],
    prompt: str,
    allowed_issue_numbers: set[str],
    authors: set[str],
    *,
    opener: Callable[..., Any] | None = None,
    timeout: int = 60,
) -> Summary:
    """Tenta cada provedor em ordem. Sem chave, erro de rede, limite de uso ou resposta recusada: passa para o próximo."""
    opener = opener or urllib.request.urlopen
    attempts: list[Attempt] = []
    for p in providers:
        key = env.get(p.key_env, "")
        if not key:
            attempts.append(Attempt(p.name, False, f"sem a chave {p.key_env}"))
            continue
        body = json.dumps(
            {
                "model": p.model,
                "temperature": 0.2,
                "max_tokens": 2500,  # o gpt-oss raciocina antes de responder, e o raciocínio conta no limite
                "messages": [{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": prompt}],
            }
        ).encode("utf-8")
        request = urllib.request.Request(f"{p.base_url.rstrip('/')}/chat/completions", data=body, method="POST")
        request.add_header("Content-Type", "application/json")
        request.add_header("Authorization", f"Bearer {key}")
        request.add_header("User-Agent", "mash-logbook/0.1")
        try:
            with opener(request, timeout=timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
            text = _clean(payload["choices"][0]["message"]["content"] or "")
        except urllib.error.HTTPError as exc:
            attempts.append(Attempt(p.name, False, f"HTTP {exc.code}"))
            continue
        except (urllib.error.URLError, socket.timeout, TimeoutError) as exc:
            attempts.append(Attempt(p.name, False, f"rede: {getattr(exc, 'reason', exc)}"))
            continue
        except (json.JSONDecodeError, UnicodeDecodeError, KeyError, IndexError, TypeError):
            attempts.append(Attempt(p.name, False, "resposta fora do formato OpenAI"))
            continue
        motivo = validate(text, allowed_issue_numbers, authors)
        if motivo:
            attempts.append(Attempt(p.name, False, f"recusada: {motivo}"))
            continue
        attempts.append(Attempt(p.name, True, "ok"))
        return Summary(text, p.name, attempts)
    return Summary(None, None, attempts)
