# Automação central de notificações do Project Mash

Esta automação acompanha o Project organizacional `Mash` e os repositórios de implementação sem instalar um workflow em cada repositório.

## Escopo monitorado

- Project: `Mash`, organização `conloq`, número `2`.
- Planejamento: `conloq/mash`.
- Código: `conloq/Back-End`, `conloq/frontend`, `conloq/landing-page-conloq`.
- Team de notificação: `@conloq/mash`.

Os cartões do Project são a unidade de contagem. Pull Requests e commits são evidências; não aumentam o total de tarefas.

## O que é avisado

- cartão que muda para `Done`;
- cartão que sai de `Done`;
- PR mesclada com referência explícita a uma Issue do planejamento;
- resumo diário às 09:00 de `America/Sao_Paulo`;
- início da Sprint;
- próxima Sprint em 3 ou 1 dias;
- Sprint terminando com tarefas restantes;
- Sprint com todos os cartões em `Done`.

## Configuração segura

A automação não deve usar o token pessoal do agente nem gravar credenciais no repositório.

### 1. Secret do repositório

Criar no repositório `conloq/.github` o Secret:

```text
MASH_PROJECT_TOKEN
```

Preferência: token de instalação de um GitHub App com permissões mínimas para ler o Project organizacional, ler PRs dos repositórios permitidos e comentar Issues somente nos destinos definidos.

Alternativa: token dedicado com acesso ao Project e aos repositórios necessários. O valor deve ser colado apenas na tela de Secret do GitHub.

### 2. Variables do repositório

Criar as Variables:

```text
MASH_NOTIFICATIONS_ENABLED=true
MASH_TRACKER_ISSUE_NUMBER=<número da Issue central>
```

A Issue central deve existir no `conloq/.github` e não deve ser adicionada ao Project Mash.

### 3. Primeira execução

Executar manualmente:

```text
Actions → Mash Project notifications → Run workflow → dry_run=true
```

O modo `dry_run` deve mostrar:

- Sprint atual;
- próxima Sprint;
- total, concluídas e restantes;
- distribuição por status e repositório;
- mensagens que seriam publicadas;
- nenhuma alteração remota.

Depois de revisar a saída, executar com `dry_run=false` uma única vez e confirmar os comentários criados. A automação lê cada comentário de volta pela API antes de considerá-lo enviado.

## Estado e deduplicação

O snapshot é mantido em um comentário técnico único na Issue central, identificado por:

```text
<!-- mash-notifier-state:v1 -->
```

Cada evento publicado recebe um marcador determinístico. Uma execução repetida não publica o mesmo evento novamente.

## Desenvolvimento local

```bash
python3 -m pytest -q tests/mash_project_notifier
python3 -m compileall -q automation
MASH_PROJECT_TOKEN=<token somente no ambiente> MASH_DRY_RUN=true PYTHONPATH=. \
  python3 -m automation.mash_project_notifier.main --dry-run
```

Nunca coloque o valor do token em arquivo, commit, log ou mensagem.

## Regras de segurança

- Falha de leitura do Project bloqueia publicação live.
- Dados parciais não são apresentados como contagem completa.
- Títulos e corpos de Issues/PRs são tratados como dados; menções externas são neutralizadas.
- PR sem vínculo explícito com `conloq/mash#N` não é atribuído a uma tarefa.
- A automação não move cartões, fecha Issues, altera responsáveis, faz merge ou modifica código.
