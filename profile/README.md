# Conloq

A Conloq reúne projetos acadêmicos e de software voltados à construção de soluções acessíveis, organizadas e baseadas em tecnologia.

## Projetos

### Mash

O Mash é um Projeto Integrador acadêmico sobre o apoio ao monitoramento da mosturação e à realização do teste de iodo na produção de cerveja artesanal.

O projeto reúne:

- Backend com Node.js, Express, Sequelize e MySQL;
- Frontend web;
- Design de interfaces, protótipos e materiais visuais;
- Artigo científico e documentação;
- Processamento de imagens com Python e OpenCV como parte prevista da solução;
- Registro e rastreabilidade de receitas, lotes e análises.

Repositórios relacionados:

- [Projeto e organização das atividades](https://github.com/conloq/mash)
- [Backend](https://github.com/conloq/Back-End)
- [Frontend](https://github.com/conloq/frontend)
- [Landing page](https://github.com/conloq/landing-page-conloq)

## Organização da equipe

- **Backend:** APIs, banco de dados, regras de negócio e integrações;
- **Frontend:** telas, componentes, acessibilidade e consumo da API;
- **Design:** protótipos, identidade visual, landing page, pitch e banner;
- **Artigo e documentação:** artigo científico, referências, decisões e registros do projeto.

## Fluxo de trabalho

1. Consultar a Issue e confirmar o escopo da tarefa.
2. Atualizar a branch local `main` antes de começar.
3. Criar uma branch própria para a alteração.
4. Fazer somente as mudanças relacionadas à tarefa.
5. Executar os testes e as validações disponíveis.
6. Criar commits seguindo o padrão de Conventional Commits.
7. Enviar a branch e abrir um Pull Request para `main`.
8. Solicitar revisão de outro integrante.
9. Corrigir os comentários, resolver as conversas e aguardar a aprovação.
10. Fazer o merge somente quando os critérios do repositório forem atendidos.

Não enviar commits diretamente para `main` quando a branch estiver protegida.

## Padrão de commits

Usamos o padrão [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/).

Formato:

```text
<tipo>: <descrição curta>
```

Também é possível indicar um escopo:

```text
<tipo>(<escopo>): <descrição curta>
```

A descrição deve ser curta, objetiva, escrita em minúsculas e preferencialmente começar com um verbo no infinitivo.

### Tipos permitidos

| Tipo | Quando usar | Exemplo |
|---|---|---|
| `feat` | Nova funcionalidade | `feat: adicionar cadastro de usuário` |
| `fix` | Correção de erro | `fix: corrigir validação de temperatura` |
| `docs` | Documentação | `docs: atualizar instruções do backend` |
| `refactor` | Reorganização sem mudar o comportamento esperado | `refactor: separar regras em services` |
| `test` | Testes | `test: adicionar testes do login` |
| `style` | Formatação ou alteração visual sem mudança de lógica | `style: ajustar espaçamento da tela` |
| `chore` | Configuração e manutenção | `chore: atualizar dependências` |
| `build` | Alteração do processo de build | `build: ajustar compilação do frontend` |
| `ci` | Integração ou automação contínua | `ci: adicionar verificação do projeto` |
| `perf` | Melhoria de desempenho | `perf: reduzir consultas repetidas` |
| `revert` | Reverter um commit anterior | `revert: desfazer alteração do login` |

### Exemplos para o Mash

```text
feat: adicionar correção de blocos
fix: corrigir rota de atualização de receita
docs: explicar fluxo de criação de lote
refactor: mover regras para o service de usuário
test: validar acesso de usuário ao próprio lote
style: ajustar layout da tela de análise
```

`feat: adicionado` é compreensível, mas a forma recomendada é usar um verbo de ação, por exemplo:

```text
feat: adicionar correção de blocos
```

Para alterações incompatíveis, usar `!` após o tipo ou registrar `BREAKING CHANGE` no rodapé do commit:

```text
feat!: alterar contrato de resposta do login
```

## Padrão de branches

O nome da branch deve seguir o formato:

```text
<tipo>/<descricao-curta>
```

Use letras minúsculas, palavras separadas por hífen e uma descrição específica.

### Exemplos

```text
feat/correcao-de-blocos
fix/validacao-de-temperatura
docs/atualizar-readme
refactor/separar-services
test/adicionar-testes-de-login
chore/atualizar-dependencias
```

A branch `feat/correcao-de-blocos` está correta estruturalmente. Use `feat` quando a alteração adicionar ou modificar uma funcionalidade. Se for exclusivamente uma correção de erro já existente, prefira:

```text
fix/correcao-de-blocos
```

Quando fizer sentido, inclua o número da Issue:

```text
feat/30-migrar-api
fix/8-validar-temperatura
```

Evitar nomes genéricos:

```text
minha-branch
teste
alteracoes
branch-do-joao
```

## Exemplo completo

```bash
git checkout main
git pull origin main
git checkout -b feat/correcao-de-blocos

# fazer a alteração e executar os testes

git add caminho/do/arquivo.js
git commit -m "feat: adicionar correção de blocos"
git push -u origin feat/correcao-de-blocos
```

Depois, abrir um Pull Request para `main`, explicar o que foi alterado, informar como foi testado e solicitar revisão de outro integrante.

## Pull Requests

Cada Pull Request deve:

- indicar a Issue relacionada;
- explicar o que foi alterado;
- informar os testes executados;
- registrar limitações ou pendências;
- evitar misturar Backend, Frontend, Design e Artigo sem necessidade;
- passar pela revisão de outro integrante quando exigido pelo repositório.

Quando a alteração concluir uma Issue, usar uma referência apropriada no corpo do Pull Request, por exemplo:

```text
Closes #30
```

## Segurança

- Nunca publicar senhas, tokens, chaves de API, cookies ou arquivos `.env`;
- Não colocar credenciais em commits, Issues, Pull Requests ou documentação pública;
- Revisar código gerado por ferramentas de IA antes do commit;
- Não descrever funcionalidades como concluídas sem validação no código e nos testes;
- Registrar decisões importantes sem expor dados sensíveis.
