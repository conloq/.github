# Diário de Bordo por sprint (conloq/mash#96)

Gera o Diário de Bordo de uma sprint a partir dos commits dos sete repositórios do Mash. Os dados (quem fez, em qual repositório, qual commit, qual issue e qual PR) vêm do GitHub. A IA só redige o parágrafo de resumo, a partir desses dados.

## Como a IA é usada

- Os provedores são tentados em ordem. Sem a chave, com erro, com limite de uso esgotado ou com resposta recusada, passa para o próximo.
- Se nenhum responder, o resumo sai montado só dos dados, e o diário sai do mesmo jeito.
- A resposta é recusada se citar issue, PR ou pessoa que não está nos dados, se tiver link ou se passar de 4000 caracteres.
- Para a IA vai só uma linha por commit: data, frente, login, tipo, primeira linha da mensagem, issues e PR. E-mails e trechos com cara de chave são trocados por `[removido]` antes.

Ordem padrão (`config.py`):

| Provedor | Modelo | Secret da chave |
|---|---|---|
| Groq | `openai/gpt-oss-120b` | `GROQ_API_KEY` |
| OpenRouter | `google/gemma-4-31b-it:free` | `OPENROUTER_API_KEY` |

As chaves ficam nos secrets de Actions do `conloq/.github` (decisão de 23/10/2026: só esses dois provedores).

Os nomes de modelo dos planos gratuitos mudam. Para trocar a lista sem mexer no código, defina `LOGBOOK_LLM_PROVIDERS` com uma lista JSON de `{"name", "base_url", "model", "key_env"}`. Qualquer provedor compatível com a API da OpenAI (`POST {base_url}/chat/completions`) funciona.

Commits feitos sem a conta do GitHub ligada ao e-mail chegam só com o nome do autor. Os nomes conhecidos viram login pelo mapa `AUTHOR_ALIASES`; outros entram por `LOGBOOK_AUTHOR_ALIASES` (objeto JSON `"nome": "login"`). Commits de robôs (`[bot]`) e de merge ficam de fora.

## Testar localmente

Não publica nada: só gera o arquivo.

```bash
# sem IA: confere a coleta
GITHUB_TOKEN=$(gh auth token) python3 -m automation.mash_logbook.main \
  --since 2026-10-08 --until 2026-10-14 --no-ai --output diario.md

# com IA: exporte as chaves que tiver (nunca as coloque em arquivo versionado)
export GROQ_API_KEY=...        # https://console.groq.com/keys
GITHUB_TOKEN=$(gh auth token) python3 -m automation.mash_logbook.main \
  --since 2026-10-08 --until 2026-10-14 --output diario.md
```

Sem `--since` e `--until`, usa a semana anterior (segunda a domingo, horário de São Paulo). No fim, o terminal mostra qual provedor foi usado e por que os outros foram pulados, sem mostrar chave.

Com `--sprint`, as datas vêm do campo `Sprint` do Project Mash (conloq #2) e só entram as sprints já encerradas cujo diário ainda não está publicado:

```bash
GITHUB_TOKEN=$(gh auth token) python3 -m automation.mash_logbook.main --sprint --no-ai
```

Cada sprint usa `startDate + duration - 1` como último dia, inclusive, e fica elegível a partir do dia seguinte. O fuso é `America/Sao_Paulo`. `--sprint` não combina com `--since`/`--until` nem com `--output`: cada sprint gera seu próprio arquivo.

## Publicação

Com `--publish`, o diário vai para `diario-de-bordo/AAAA-MM-DD.md` (data do primeiro dia) no `conloq/logbook-backup`, numa branch `diario-de-bordo/AAAA-MM-DD`, com Pull Request para revisão. Rodar de novo para a mesma sprint atualiza o arquivo no mesmo PR. O commit do diário começa com `docs(diario-de-bordo):` e fica fora da coleta das sprints seguintes.

O workflow `.github/workflows/mash-logbook.yml` roda todo dia às 09:00 de São Paulo e publica só as sprints encerradas sem diário no branch padrão: um PR por sprint pendente, em ordem cronológica, sem PR diário. Se uma execução for perdida, a sprint continua elegível nos dias seguintes até o arquivo aparecer no branch padrão. Arquivo já publicado não gera outro PR.

Pelo Actions, "Run workflow" aceita `since`, `until` e `dry_run`: com `dry_run` marcado (padrão), o diário só aparece no resumo da execução; datas explícitas geram aquele intervalo em vez das sprints. O `MASH_PROJECT_TOKEN` precisa poder ler o Project Mash e criar branch e Pull Request no `conloq/logbook-backup`. Se a leitura do Project ou do repositório de destino falhar, a execução termina em erro, sem publicar um período inferido.

Para verificar se `MASH_PROJECT_TOKEN` também pode ler o Project Mash, rode o workflow manualmente com `check_project_access` marcado. Essa opção testa a leitura do campo `Sprint`, não gera nem publica diário e não altera o Project.

## Testes

```bash
python -m pytest -q tests/mash_logbook
```
