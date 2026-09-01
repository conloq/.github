from __future__ import annotations

import json
import re
from typing import Any

STATE_MARKER = "<!-- mash-notifier-state:v1 -->"
_EVENT_MARKER_PREFIX = "<!-- mash-notifier:event:"
_EVENT_MARKER_SUFFIX = " -->"


def encode_state(state: dict[str, Any]) -> str:
    """Encode non-secret state in one machine-readable HTML comment block."""
    payload = json.dumps(state, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return f"{STATE_MARKER}\n```json\n{payload}\n```"


def decode_state(body: str) -> dict[str, Any] | None:
    """Decode the latest state block, returning None for absent/invalid data."""
    if STATE_MARKER not in body:
        return None
    after = body.split(STATE_MARKER, 1)[1]
    match = re.search(r"```json\s*(\{.*?\})\s*```", after, flags=re.DOTALL)
    if not match:
        return None
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError:
        return None
    return value if isinstance(value, dict) else None


def event_marker(key: str) -> str:
    return f"{_EVENT_MARKER_PREFIX}{key}{_EVENT_MARKER_SUFFIX}"


def extract_event_keys(body: str) -> set[str]:
    pattern = re.escape(_EVENT_MARKER_PREFIX) + r"(.*?)" + re.escape(_EVENT_MARKER_SUFFIX)
    return set(re.findall(pattern, body, flags=re.DOTALL))
