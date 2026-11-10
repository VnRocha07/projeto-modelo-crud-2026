# 📦 Estoque: projeto modelo do intensivão

Projeto de referência para as UCs **Garantia da Qualidade de Software** e **Banco de Dados**
(UNIFG 2026/2). Mostra, num sistema pequeno e completo, tudo o que o projeto de vocês precisa ter:

| Requisito | Onde está aqui |
|---|---|
| **Banco de dados SQL** | [`db/`](db/): esquema MySQL 8.4 (e o mesmo em SQLite), seed, PK, FK, UNIQUE, CHECK, `DECIMAL` |
| **CRUD** | tela em [`web/`](web/) + rotas `GET/POST/PUT/DELETE` em [`api/app/main.py`](api/app/main.py) |
| **API em Python** | FastAPI + SQL escrito à mão em [`api/app/repositorio.py`](api/app/repositorio.py) |
| **Testes unitários** | [`api/tests/unit/`](api/tests/unit/): regras puras e API com dublê (sem banco) |
| **Testes de integração** | [`api/tests/integracao/`](api/tests/integracao/): o SQL contra um banco de verdade |
| **Testes E2E com Cypress** | [`e2e/cypress/e2e/produtos.cy.js`](e2e/cypress/e2e/produtos.cy.js) |
| **CI** | [`.github/workflows/ci.yml`](.github/workflows/ci.yml): os três níveis a cada push |

## 📚 Por onde começar

| Guia | Para quê |
|---|---|
| **[INTENSIVO.md](INTENSIVO.md)** | o que cada equipe precisa entregar, o roteiro da aula e a rubrica |
| **[docs/PASSO-A-PASSO.md](docs/PASSO-A-PASSO.md)** | replicar este modelo no **seu** projeto, passo a passo, com conferência em cada etapa |
| **[docs/CYPRESS.md](docs/CYPRESS.md)** | Cypress do zero: seletores, asserções, reset do banco, `cy.request`, `cy.intercept`, CI |

---

## Arquitetura

```
 navegador ── web/ (HTML + JS, sem framework)
     │  fetch /api/...
     ▼
 FastAPI ──── app/main.py        rotas HTTP, códigos de status
     │        app/schemas.py     validação de entrada (Pydantic)
     │        app/regras.py      regras de negócio PURAS  ◄── teste unitário
     ▼
 app/repositorio.py  SQL: SELECT/JOIN, INSERT, UPDATE, DELETE, GROUP BY  ◄── teste de integração
     ▼
 MySQL 8.4 (Docker)  ou  SQLite (sem Docker)

 Cypress ── dirige o navegador de ponta a ponta  ◄── teste E2E
```

### O modelo de dados

```
categoria                     produto
─────────                     ───────────────────────────────
id   PK                       id            PK
nome UNIQUE   1 ────────< N   sku           UNIQUE, formato AAA-000
                              nome
                              preco         DECIMAL(10,2), CHECK >= 0
                              quantidade    INT, CHECK >= 0
                              categoria_id  FK -> categoria.id (RESTRICT)
                              criado_em
```

---

## Como rodar

Pré-requisitos: **Python 3.13** com [`uv`](https://docs.astral.sh/uv/), **Node 20+**, e
**Docker** (opcional: sem ele, a API usa SQLite).

### Opção A: com Docker (MySQL 8.4, o motor da disciplina de BD)

```bash
docker compose up --build
```

Abra <http://localhost:8000>. A documentação interativa da API fica em <http://localhost:8000/docs>.

Para entrar no banco:

```bash
docker compose exec db mysql -uapp -papp estoque
```

### Opção B: sem Docker (SQLite)

```bash
cd api
uv sync
APP_ENV=test uv run uvicorn app.main:app --reload
```

O arquivo `api/estoque.db` é criado e populado na primeira execução.

---

## Testes

### Unitários e integração (pytest)

```bash
cd api
uv run pytest                  # tudo
uv run pytest tests/unit       # só unitários (não tocam em banco)
uv run pytest -m integracao    # só integração
uv run pytest --cov            # com cobertura
```

Integração no MySQL, com o `docker compose` de pé:

```bash
DATABASE_URL="mysql+pymysql://app:app@127.0.0.1:3306/estoque?charset=utf8mb4" uv run pytest -m integracao
```

### E2E (Cypress)

A API precisa estar rodando com `APP_ENV=test`: é isso que habilita a rota
`POST /api/_test/reset`, que o Cypress chama antes de cada teste para voltar ao seed.

```bash
cd e2e
npm install
npm run e2e        # sobe a API (SQLite), espera ficar de pé, roda o Cypress e derruba
```

Ou, com a API já rodando (Docker ou Opção B):

```bash
npm run cy:open    # interface gráfica: escolha E2E Testing > Chrome > produtos.cy.js
npm run cy:run     # headless, no terminal
```

---

## As quatro camadas de teste, lado a lado

| Camada | Arquivo | Pega o quê | Não pega |
|---|---|---|---|
| Unitário (regra) | `test_regras.py` | SKU mal formado, faixa de estoque, arredondamento | nada de HTTP nem de SQL |
| Unitário (API) | `test_api.py` | 201/404/409/422, validação de entrada | SQL errado: o banco é um dublê |
| Integração | `test_repositorio.py` | JOIN, GROUP BY, FK, UNIQUE, CHECK, `DECIMAL` | tela quebrada |
| E2E | `produtos.cy.js` | o fluxo do usuário funcionando de ponta a ponta | é lento: não serve para testar cada regra |

> 🔴 A rota `/api/_test/reset` **apaga todos os dados**. Ela só existe com `APP_ENV=test`, e
> há um teste unitário que garante isso. Nunca suba com `APP_ENV=test` em produção.
