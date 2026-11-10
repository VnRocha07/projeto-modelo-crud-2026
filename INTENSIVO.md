# 🚀 Intensivão: do banco ao Cypress

**UCs:** Garantia da Qualidade de Software · Banco de Dados — UNIFG 2026/2
**Prof.:** Petros Barreto

Cada equipe apresenta **um projeto próprio** com um CRUD de verdade. Este repositório é o
**modelo**: tudo o que se pede aqui está implementado nele, funcionando, para consulta.

> Não copie o domínio. O "Estoque" é só o exemplo. Escolha o seu: agenda de consultas,
> controle de academia, cardápio de restaurante, inventário de laboratório…

---

## ✅ O mínimo que o projeto precisa ter

### Banco de dados (avaliado em Banco de Dados)

- [ ] **Ao menos 2 tabelas relacionadas** por chave estrangeira (1:N)
- [ ] Chave primária em todas as tabelas
- [ ] Ao menos **1 `UNIQUE`** e **1 `CHECK`** com sentido de negócio
- [ ] Tipo correto para cada coluna (dinheiro é `DECIMAL`, nunca `FLOAT`)
- [ ] Script de esquema (`CREATE TABLE`) e script de carga (seed) **versionados no repositório**
- [ ] Ao menos **1 consulta com `JOIN`** e **1 com `GROUP BY`** usadas pela aplicação
- [ ] SQL com **parâmetros**, nunca concatenando texto do usuário na consulta

### API e CRUD

- [ ] API em **Python** (FastAPI, Flask ou Django) conectada ao banco SQL
- [ ] **C**reate, **R**ead, **U**pdate e **D**elete de ao menos uma entidade
- [ ] Códigos HTTP corretos: `201` ao criar, `204` ao excluir, `404` inexistente,
      `409` conflito, `422` entrada inválida
- [ ] Uma tela (web) que use o CRUD inteiro

### Testes (avaliado em Garantia da Qualidade)

- [ ] **Testes unitários** com `pytest`: ao menos **5**, cobrindo uma regra de negócio,
      com **valor-limite** em pelo menos uma
- [ ] Ao menos **1 teste de integração** que fale com o banco de verdade
- [ ] **Testes E2E com Cypress** cobrindo as **4 operações do CRUD** e **1 caminho de erro**
- [ ] Seletores `data-cy` no HTML (não selecionar por classe CSS nem por texto)
- [ ] Cada teste E2E parte de um **estado conhecido** do banco (reset/seed antes de cada um)
- [ ] `README.md` com os comandos para subir o sistema e rodar cada suíte

### Bônus

- [ ] CI no GitHub Actions rodando as suítes a cada push
- [ ] Cobertura ≥ 80 % (`pytest --cov`)
- [ ] `docker compose up` sobe tudo

---

## 🗺️ Roteiro do intensivão

Cada etapa tem um **checkpoint**: um comando e a saída que você deve ver. Se a sua saída
for diferente, pare e resolva antes de seguir.

### Etapa 0 — Ambiente e modelo rodando (30 min)

```bash
git clone <url-deste-repo> && cd projeto-modelo-crud-2026/api
uv sync
uv run pytest -q
```

**Checkpoint:**

```
43 passed
```

Depois: `APP_ENV=test uv run uvicorn app.main:app --reload` e abra <http://localhost:8000>.
Crie, edite e exclua um produto pela tela. Abra <http://localhost:8000/docs> e chame
`GET /api/produtos/1` pelo "Try it out".

### Etapa 1 — O banco do SEU projeto (1h)

Referência: [`db/mysql/01-schema.sql`](db/mysql/01-schema.sql) e [`db/seed.sql`](db/seed.sql).

1. Desenhe as entidades e o relacionamento 1:N no papel (ou no dbdiagram.io).
2. Escreva o `CREATE TABLE` com PK, FK, `UNIQUE` e `CHECK`.
3. Escreva o seed com 5 a 10 linhas. **Ele começa com `DELETE`**, para poder ser reexecutado.
4. Rode no MySQL e prove que as restrições funcionam: tente inserir algo que viole cada uma.

**Checkpoint** (no modelo, inserindo SKU repetido):

```bash
docker compose exec db mysql -uapp -papp estoque -e \
  "INSERT INTO produto (sku, nome, preco, quantidade, categoria_id) VALUES ('ELE-001', 'Repetido', 1.00, 1, 1)"
```
```
ERROR 1062 (23000) at line 1: Duplicate entry 'ELE-001' for key 'produto.uq_produto_sku'
```

(No cliente interativo `mysql>`, a mesma linha aparece sem o `at line 1`.)

### Etapa 2 — API e CRUD (1h30)

Referência: [`api/app/main.py`](api/app/main.py) e [`api/app/repositorio.py`](api/app/repositorio.py).

1. Uma rota por operação: `GET` lista, `GET /{id}`, `POST`, `PUT /{id}`, `DELETE /{id}`.
2. O SQL fica no repositório; a rota só decide o código HTTP.
3. Valide a entrada com Pydantic (`schemas.py`): é ele quem devolve o `422`.

**Checkpoint** (no modelo):

```bash
curl -s localhost:8000/api/produtos/1
```
```
{"id":1,"sku":"ELE-001","nome":"Mouse sem fio","preco":"79.90","quantidade":12,"categoria_id":1,"categoria":"Eletrônicos","status":"ok"}
```

```bash
curl -s -X POST localhost:8000/api/produtos -H 'Content-Type: application/json' \
  -d '{"sku":"ELE-001","nome":"x y","preco":"1","quantidade":1,"categoria_id":1}' -w " %{http_code}\n"
```
```
{"detail":"SKU ELE-001 ja cadastrado"} 409
```

### Etapa 3 — Testes unitários e de integração (1h)

Referência: [`api/tests/`](api/tests/).

1. **Extraia uma regra de negócio para uma função pura** (como `status_estoque` em
   [`regras.py`](api/app/regras.py)). Função pura é a mais fácil de testar.
2. Teste as **bordas**: se a regra muda em 5, teste 4, 5 e 6.
3. Teste a API **sem banco**, trocando o repositório por um dublê
   (`app.dependency_overrides`, ver [`test_api.py`](api/tests/unit/test_api.py)).
4. Escreva ao menos um teste de integração que prove uma restrição do banco.

**Checkpoint** (no modelo):

```bash
uv run pytest tests/unit -q
```
```
33 passed
```

```bash
uv run pytest -m integracao -q
```
```
10 passed, 33 deselected
```

### Etapa 4 — Cypress (1h30)

Referência: [`e2e/`](e2e/).

1. Coloque `data-cy="..."` em todo elemento que o teste vai tocar.
2. Crie uma rota de reset **só para ambiente de teste** e chame no `beforeEach`.
3. Um `it(...)` por operação do CRUD, mais um para um erro (duplicado, campo inválido).
4. Use `cy.on("window:confirm", ...)` se a exclusão pedir confirmação.

```bash
cd e2e
npm install
npm run e2e
```

**Checkpoint:** todos os testes de `produtos.cy.js` verdes (12 testes em 4 `describe`).

### Etapa 5 — CI (bônus, 30 min)

Copie [`.github/workflows/ci.yml`](.github/workflows/ci.yml), ajuste os caminhos e faça push.
**Checkpoint:** os três jobs verdes na aba **Actions** do GitHub.

---

## 🎤 A apresentação (10 min por equipe)

| Tempo | O que mostrar |
|---|---|
| 1 min | O problema e o domínio |
| 2 min | O modelo de dados: as tabelas, a FK, e **uma restrição sendo violada ao vivo** |
| 2 min | O CRUD funcionando na tela: criar, editar, excluir |
| 2 min | `pytest` rodando ao vivo + **um teste de valor-limite explicado** |
| 2 min | `cypress open` rodando os testes E2E na frente da turma |
| 1 min | Um defeito que os testes pegaram durante o desenvolvimento |

### Rubrica (10 pontos)

| Critério | Pontos | Nota máxima quando… |
|---|---|---|
| Modelagem e SQL | 2,5 | FK, PK, UNIQUE, CHECK e tipos corretos; JOIN e GROUP BY usados de verdade |
| CRUD e API | 2,0 | as 4 operações funcionam; códigos HTTP corretos; SQL parametrizado |
| Testes unitários e integração | 2,0 | ≥ 5 unitários com valor-limite; ≥ 1 integração; tudo verde |
| Testes E2E (Cypress) | 2,5 | CRUD inteiro + 1 erro; `data-cy`; estado resetado antes de cada teste |
| Apresentação e README | 1,0 | dentro do tempo; o README permite rodar o projeto do zero |

---

## 🚑 Se der errado

| Mensagem | Causa provável | O que fazer |
|---|---|---|
| `ModuleNotFoundError: No module named 'app'` | `pytest` rodado fora da pasta `api/` | `cd api` antes |
| `Can't connect to MySQL server on '127.0.0.1'` | contêiner ainda subindo | espere o `healthy` em `docker compose ps` |
| `Cypress could not verify that this server is running` | API não está de pé | suba a API antes, ou use `npm run e2e` |
| `cy.request() failed ... 404` em `/api/_test/reset` | API subiu sem `APP_ENV=test` | suba com `APP_ENV=test` |
| Teste E2E passa sozinho e falha em conjunto | um teste depende do que o anterior deixou | reset no `beforeEach` |
| `Error binding parameter` no SQLite | `Decimal` passado direto ao driver | converta para `str` (ver `_parametros` no repositório) |
| `npm run e2e` falha no Windows | o script usa sintaxe de shell Unix | rode no Git Bash ou no WSL, ou use o Codespaces |
