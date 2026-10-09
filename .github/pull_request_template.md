## Tipo de Alteração

- [ ] Nova funcionalidade (`feat`)
- [ ] Correção de bug (`fix`)
- [ ] Refatoração ou melhoria técnica (`refactor`)
- [ ] Atualização de documentação (`docs`)

## Issue Relacionada

Closes conloq/mash#<!-- Número da issue, ex.: Closes conloq/mash#32. Use Fixes para bug. -->

## Descrição das Alterações

<!-- Descreva de forma concisa o que foi desenvolvido ou corrigido nesta entrega. -->

## Checklist da Definição de Pronto (DoD)

- [ ] O código foi executado sem erros ou warnings no console.
- [ ] A mudança cobre só o escopo da issue, sem "caronas".
- [ ] Validação manual feita nos caminhos de sucesso e de erro, com a evidência registrada na conloq/mash#41 quando a mudança cria ou altera rota.
- [ ] Não há dados sensíveis (senhas, chaves de API, `.env`) nem `node_modules` incluídos nos commits.
- [ ] As respostas seguem o contrato da issue: códigos HTTP, `{ "message": ... }` no sucesso, `{ "error": ... }` no erro e JSON em camelCase.
- [ ] A documentação da API (Swagger) e o README foram atualizados, se aplicável.

## Evidências de Teste

<!-- Backend: método, rota, status e JSON de resposta, sem token nem senha. Frontend: captura de tela. -->
