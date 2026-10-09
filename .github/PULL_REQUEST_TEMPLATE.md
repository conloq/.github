## O que muda

<!-- Explique a mudança em duas ou três frases. -->

Closes conloq/mash#

<!-- Use "Closes" para funcionalidade ou tarefa e "Fixes" para bug. As issues ficam em conloq/mash. -->

## Tipo de mudança

- [ ] Funcionalidade nova
- [ ] Correção de bug
- [ ] Refatoração, sem mudança de comportamento
- [ ] Documentação

## Checklist (DoD)

- [ ] A mudança cobre só o escopo da issue.
- [ ] O código roda sem erro e não deixa `console.log` de depuração.
- [ ] Nenhum segredo, `.env` ou `node_modules` entrou no commit.
- [ ] As respostas seguem o contrato da issue: códigos HTTP, `{ "message": ... }` no sucesso, `{ "error": ... }` no erro e JSON em camelCase.
- [ ] Validação manual feita, nos caminhos de sucesso e de erro.
- [ ] Evidência registrada na conloq/mash#41, quando a mudança cria ou altera rota.
- [ ] Documentação e Swagger atualizados, quando o contrato mudou.

## Evidência

<!-- Backend: método, rota, status e JSON de resposta, sem token nem senha. Frontend: captura de tela. -->
