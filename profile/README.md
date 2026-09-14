# Conloq

A Conloq desenvolve soluções multiplataforma para o ecossistema das cervejarias artesanais. Com o Mash, produtores acompanham informações importantes da mosturação e analisam seus registros com mais clareza.

O foco atual é apoiar o acompanhamento de temperatura, o teste de iodo e o registro das análises, sem substituir a validação do processo pelo produtor.

## Projetos

### Mash

O Mash é um projeto acadêmico chamado Projeto Integrador. Ele funciona como o trabalho de conclusão do curso, de forma semelhante a um TCC, e trata do apoio ao monitoramento da mosturação e à realização do teste de iodo na produção de cerveja artesanal.

O projeto reúne:

- Backend com Node.js, Express, Sequelize, MySQL, JWT e Argon2id;
- Frontend web com Tailwind CSS;
- Design de interfaces, protótipos e materiais visuais;
- Artigo científico e documentação;
- Processamento de imagens com Python e OpenCV como parte prevista da solução;
- Registro e rastreabilidade de receitas, lotes e análises;
- Automação de notificações de sprint com GitHub Actions e Python.

Repositórios relacionados:

- [Projeto e organização das atividades](https://github.com/conloq/mash)
- [Backend — API REST](https://github.com/conloq/Back-End)
- [Frontend — preview com Tailwind](https://github.com/conloq/frontend)
- [Landing page](https://github.com/conloq/landing-page-conloq)
- [Documentação do banco de dados](https://github.com/conloq/database)
- [Documentação do projeto](https://github.com/conloq/documentation)

## Organização da equipe

- **Backend:** APIs, banco de dados, regras de negócio, autenticação JWT/Argon2id e integrações;
- **Frontend:** telas, componentes Tailwind, acessibilidade e consumo da API REST;
- **Design:** protótipos Figma, identidade visual, landing page, pitch e banner;
- **Artigo e documentação:** artigo científico, referências, SWOT, decisões e registros do projeto.

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

Não enviar commits diretamente para `main`.

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
feat: adicionar CRUD de lotes
feat: implementar upload de imagem do teste de iodo
fix: corrigir referência de id no controller de receitas
fix: corrigir validação de temperatura
docs: documentar contrato de temperatura e teste de iodo
refactor: migrar autenticação de session para JWT
test: adicionar testes do CRUD de lotes
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

Quando fizer sentido, inclua o número da Issue:

```text
feat/30-migrar-api
fix/38-corrigir-autenticacao
feat/31-implementar-crud-lotes
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
git checkout -b feat/31-implementar-crud-lotes

# fazer a alteração e executar os testes

git add caminho/do/arquivo.js
git commit -m "feat: implementar CRUD de lotes"
git push -u origin feat/31-implementar-crud-lotes
```

Depois, abrir um Pull Request para `main`, explicar o que foi alterado, informar como foi testado e solicitar revisão de outro integrante.

## Pull Requests

Cada Pull Request deve:

- indicar a Issue relacionada;
- explicar o que foi alterado;
- informar os testes executados;
- registrar limitações ou pendências;
- evitar misturar Backend, Frontend, Design e Artigo sem necessidade;
- passar pela revisão de outro integrante.

Quando a alteração concluir uma Issue, usar uma referência apropriada no corpo do Pull Request, por exemplo:

```text
Closes #31
```

## Segurança

- Nunca publicar senhas, tokens, chaves de API, cookies ou arquivos `.env`;
- Não colocar credenciais em commits, Issues, Pull Requests ou documentação pública;
- Revisar código gerado por ferramentas de IA antes do commit;
- Não descrever funcionalidades como concluídas sem validação no código e nos testes;
- Registrar decisões importantes sem expor dados sensíveis;
- Usar variáveis de ambiente (`.env`) para configurações locais e adicionar `.env` ao `.gitignore`.

## Documentação

A documentação completa do projeto está disponível no repositório [conloq/documentation](https://github.com/conloq/documentation), organizada por área:

| Área | Conteúdo |
|---|---|
| [Backend](https://github.com/conloq/documentation/tree/main/backend) | Arquitetura, models, rotas, issues ativas |
| [Frontend](https://github.com/conloq/documentation/tree/main/frontend) | Preview, componentes, integração com API |
| [Database](https://github.com/conloq/documentation/tree/main/database) | Schema MySQL, MER, SQL, divergências de schema |
| [Artigo](https://github.com/conloq/documentation/tree/main/artigo) | Artigo científico, metas de validação, referências |
| [Design](https://github.com/conloq/documentation/tree/main/design) | Guia de estilos, Figma, pitch, landing page |
| [Infraestrutura](https://github.com/conloq/documentation/tree/main/infraestrutura) | Rede, DevOps, automação |
| [Geral](https://github.com/conloq/documentation/tree/main/geral) | Decisões técnicas, entregas do PI, boas práticas |
