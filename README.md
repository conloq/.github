# .github

Repositório especial da organização [Conloq](https://github.com/conloq). O README que aparece no perfil da organização está em [profile/README.md](profile/README.md) — papéis da squad (PO, PM e Devs), fluxo de trabalho, padrões de commits/branches/PRs e links dos repositórios.

## Conteúdo

- [profile/README.md](profile/README.md) — perfil público da organização.
- [automation/](automation/) — automação de notificações de sprint (GitHub Actions + Python).
- [tests/](tests/) — testes da automação.

## Modelo de Pull Request

O arquivo `.github/pull_request_template.md` deste repositório é o modelo de Pull Request da organização. O GitHub preenche a descrição de todo Pull Request novo com ele, em qualquer repositório público da `conloq` que não tenha um modelo próprio. O `Testes-Automatizados-GAPS` tem o dele e não é afetado.

O modelo segue o laboratório da aula 08 de GAPS (Auditoria de Pull Requests e Revisão de Código), com as mesmas cinco seções:

1. **Tipo de Alteração:** marque uma opção; ela deve bater com o prefixo do título (`feat`, `fix`, `refactor` ou `docs`).
2. **Issue Relacionada:** `Closes conloq/mash#N`. As issues ficam em `conloq/mash`, por isso o nome do repositório vai junto. A issue fecha sozinha no merge.
3. **Descrição das Alterações:** o que mudou e por quê, em poucas linhas.
4. **Checklist da Definição de Pronto (DoD):** marque só o que foi feito. Item que não se aplica fica desmarcado, com uma nota.
5. **Evidências de Teste:** JSON de resposta no backend, captura de tela no frontend. Sem token nem senha.

Duas diferenças em relação ao modelo da aula, por decisão do projeto: a validação é manual, registrada na issue conloq/mash#41, no lugar dos testes automatizados; e não há item de linter, porque os repositórios não têm um configurado.

Quem revisa segue as cinco etapas da mesma aula: rastreabilidade com a issue, higiene do Git, qualidade do código, evidências e parecer (Comment, Request changes ou Approve).

Para mudar o modelo, edite o arquivo por branch `docs/...` e Pull Request neste repositório. Um repositório que precise de um modelo diferente cria o seu próprio `.github/pull_request_template.md`.
