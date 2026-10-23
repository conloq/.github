from __future__ import annotations

import base64
from datetime import date
from urllib.parse import quote

from automation.mash_project_notifier.github_client import GitHubAPIError

from . import config


def _get_or_none(client, path: str):
    try:
        return client.rest("GET", path)
    except GitHubAPIError as exc:
        if "HTTP 404" in str(exc):
            return None
        raise


def publish(client, markdown: str, since: date, until: date, repository: str = config.LOGBOOK_REPOSITORY) -> str:
    """Grava o diário numa branch do repositório de documentação e abre (ou reaproveita) o Pull Request.

    Rodar de novo para a mesma semana atualiza o arquivo na mesma branch e no mesmo PR. Devolve a URL do PR.
    """
    periodo = f"{since:%d/%m} a {until:%d/%m/%Y}"
    path = f"{config.LOGBOOK_DIR}/{since:%Y-%m-%d}.md"
    branch = f"diario-de-bordo/{since:%Y-%m-%d}"
    base = client.rest("GET", f"/repos/{repository}")["default_branch"]

    if _get_or_none(client, f"/repos/{repository}/git/ref/heads/{quote(branch)}") is None:
        sha = client.rest("GET", f"/repos/{repository}/git/ref/heads/{quote(base)}")["object"]["sha"]
        client.rest("POST", f"/repos/{repository}/git/refs", {"ref": f"refs/heads/{branch}", "sha": sha})

    payload = {
        "message": f"{config.COMMIT_PREFIX} {periodo}",
        "content": base64.b64encode(markdown.encode("utf-8")).decode("ascii"),
        "branch": branch,
    }
    existing = _get_or_none(client, f"/repos/{repository}/contents/{quote(path)}?ref={quote(branch, safe='')}")
    if existing:
        payload["sha"] = existing["sha"]
    client.rest("PUT", f"/repos/{repository}/contents/{quote(path)}", payload)

    owner = repository.split("/")[0]
    pulls = client.rest("GET", f"/repos/{repository}/pulls?state=open&head={quote(f'{owner}:{branch}', safe='')}") or []
    if pulls:
        return pulls[0]["html_url"]
    body = (
        f"Diário de Bordo de {periodo}, gerado pelo workflow `mash-logbook` do `conloq/.github` (conloq/mash#96).\n\n"
        "Revise o resumo antes de mesclar: quando ele foi redigido por IA, o arquivo diz qual provedor foi usado."
    )
    pull = client.rest(
        "POST",
        f"/repos/{repository}/pulls",
        {"title": f"docs: Diário de Bordo de {periodo}", "head": branch, "base": base, "body": body},
    )
    return pull["html_url"]
