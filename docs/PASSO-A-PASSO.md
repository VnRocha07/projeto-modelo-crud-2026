# 🧭 Passo a passo: replicar o modelo no SEU projeto

Siga na ordem. Cada passo diz **o que fazer**, **qual arquivo do modelo copiar/adaptar** e
**como conferir** antes de seguir. Não pule o "Confira": é ele que mostra que você saiu do
trilho enquanto ainda é fácil voltar.

Durante todo o guia, troque:

| No modelo | No seu projeto (exemplo: academia) |
|---|---|
| `categoria` | a tabela "pai" (`plano`) |
| `produto` | a tabela "filha", a do CRUD (`aluno`) |
| `sku` | o campo único de negócio (`cpf`, `matricula`, `email`) |
| `quantidade`, `preco` | os campos com regra (`idade`, `mensalidade`) |

---

## Passo 0 — Ferramentas (15 min)

Instale e confira cada uma:

```bash
git --version
python3 --version      # 3.12 ou mais novo
uv --version           # https://docs.astral.sh/uv/  ->  curl -LsSf https://astral.sh/uv/install.sh | sh
node --version         # 20 ou mais novo
docker --version       # opcional: sem ele, use SQLite
```

Sem Docker ou com a máquina travada? Use o **GitHub Codespaces** (botão verde **Code** →
**Codespaces** → **Create codespace**): já vem com Python, Node e Docker.

---

## Passo 1 — Rodar o modelo antes de tudo (15 min)

Você só consegue copiar o que viu funcionando.

```bash
git clone https://github.com/petrosbarreto/projeto-modelo-crud-2026.git
cd projeto-modelo-crud-2026/api
uv sync
uv run pytest -q
```

**Confira:** a última linha é `43 passed`.

```bash
APP_ENV=test uv run uvicorn app.main:app --reload
```

**Confira:** <http://localhost:8000> mostra a tela do Estoque; <http://localhost:8000/docs>
mostra a documentação da API. Crie, edite e exclua um produto.

---

## Passo 2 — Criar o repositório e as pastas (10 min)

No GitHub, crie o repositório do seu projeto (com README). Clone e crie a mesma estrutura do
modelo:

```bash
git clone https://github.com/<voce>/<seu-projeto>.git
cd <seu-projeto>
mkdir -p api/app api/tests/unit api/tests/integracao db/mysql db/sqlite web e2e
touch api/app/__init__.py
```

Copie o [`.gitignore`](../.gitignore) do modelo para a raiz.

```
<seu-projeto>/
├── api/          a API em Python e os testes pytest
├── db/           os scripts SQL
├── web/          a tela (HTML + JS)
├── e2e/          os testes Cypress
└── docker-compose.yml
```

**Confira:** `git status` mostra a pasta nova e o `.gitignore`. Faça o primeiro commit.

---

## Passo 3 — O banco (45 min)

### 3.1 Modele no papel

Duas tabelas, ligadas por chave estrangeira (1:N). Para cada coluna, decida o tipo e a
restrição. Exemplo da academia:

```
plano                         aluno
─────                         ───────────────────────────
id   PK                       id           PK
nome UNIQUE   1 ────────< N   cpf          UNIQUE
mensalidade DECIMAL(10,2)     nome         NOT NULL
                              idade        CHECK (idade >= 14)
                              plano_id     FK -> plano.id
```

### 3.2 Escreva o esquema

Copie [`db/mysql/01-schema.sql`](../db/mysql/01-schema.sql) para `db/mysql/01-schema.sql` e
adapte. Mantenha:

- `CONSTRAINT pk_...`, `uq_...`, `ck_...`, `fk_...` **com nome**: a mensagem de erro fica legível;
- `ENGINE = InnoDB DEFAULT CHARSET = utf8mb4`;
- `DECIMAL(10, 2)` para dinheiro.

Se for usar SQLite também, faça a versão [`db/sqlite/01-schema.sql`](../db/sqlite/01-schema.sql)
(diferença principal: `INTEGER PRIMARY KEY AUTOINCREMENT` no lugar de `INT ... AUTO_INCREMENT`).

### 3.3 Escreva o seed

Copie [`db/seed.sql`](../db/seed.sql) e adapte. Regras:

1. **Começa com `DELETE`** da filha e depois da pai (nessa ordem, por causa da FK).
2. `INSERT` com **ids fixos** (`(1, ...)`, `(2, ...)`): os testes vão usar esses ids.
3. Entre 5 e 10 linhas na tabela filha, com dados que exercitem as regras (um com estoque
   zerado, um no limite, etc.).

### 3.4 Suba o MySQL

Copie [`docker-compose.yml`](../docker-compose.yml) para a raiz. Troque `estoque` pelo nome do
seu banco. Por enquanto, comente o serviço `api` (ele ainda não existe):

```bash
docker compose up -d db
docker compose exec db mysql -uapp -papp <seu_banco> -e "SHOW TABLES"
```

**Confira:** aparecem as suas duas tabelas. Prove cada restrição tentando violá-la:

```bash
docker compose exec db mysql -uapp -papp <seu_banco> -e "INSERT INTO aluno (cpf, nome, idade, plano_id) VALUES ('111', 'Repetido', 20, 1)"
```

Você deve ver um `ERROR 1062 (23000)` (UNIQUE), `ERROR 3819` (CHECK) ou `ERROR 1452` (FK).
Guarde essas saídas: vão para a apresentação.

> Mudou o `01-schema.sql` e quer recriar? Os scripts só rodam com o volume vazio:
> `docker compose down -v && docker compose up -d db`.

---

## Passo 4 — A API em Python (1h30)

### 4.1 Projeto e dependências

```bash
cd api
uv init --bare
uv add fastapi "uvicorn[standard]" sqlalchemy pymysql cryptography
uv add --dev pytest pytest-cov httpx
```

Copie a seção `[tool.pytest.ini_options]` do [`api/pyproject.toml`](../api/pyproject.toml) do
modelo para o seu (ela tem o `pythonpath = ["."]`, sem ela o pytest não acha o pacote `app`).

### 4.2 Os arquivos, um por responsabilidade

Copie cada arquivo do modelo e adapte **nesta ordem**:

| Ordem | Arquivo | O que adaptar |
|---|---|---|
| 1 | [`app/db.py`](../api/app/db.py) | nada: funciona como está (lê `DATABASE_URL`) |
| 2 | [`app/regras.py`](../api/app/regras.py) | as **suas** regras de negócio como funções puras (`validar_cpf`, `faixa_etaria`) |
| 3 | [`app/schemas.py`](../api/app/schemas.py) | os campos da sua entidade; os `field_validator` chamam as funções de `regras.py` |
| 4 | [`app/repositorio.py`](../api/app/repositorio.py) | o SQL: troque `produto`/`categoria` pelas suas tabelas e colunas |
| 5 | [`app/main.py`](../api/app/main.py) | as rotas: troque `/api/produtos` por `/api/alunos` |

Três regras que **não** se adaptam, se copiam:

1. **SQL sempre com parâmetro nomeado** (`WHERE id = :id`, e o valor num dicionário). Nunca
   `f"... WHERE id = {id}"`: isso é SQL injection.
2. **A rota não tem SQL**: ela chama o repositório e decide o código HTTP (201, 404, 409, 422).
3. **A rota de reset só existe com `APP_ENV=test`** (o `if os.getenv("APP_ENV") == "test":` no
   fim do `main.py`).

### 4.3 Rode

```bash
APP_ENV=test DATABASE_URL="mysql+pymysql://app:app@127.0.0.1:3306/<seu_banco>?charset=utf8mb4" \
  uv run uvicorn app.main:app --reload
```

(Sem Docker: só `APP_ENV=test uv run uvicorn app.main:app --reload`, e ele usa SQLite.)

**Confira** em <http://localhost:8000/docs>, no "Try it out", **as 5 rotas**:

| Chamada | Resposta esperada |
|---|---|
| `GET /api/<coisas>` | `200` com a lista do seed |
| `GET /api/<coisas>/1` | `200`; e com `/999`: `404` |
| `POST /api/<coisas>` com dado válido | `201`; repetindo o mesmo: `409` |
| `PUT /api/<coisas>/1` | `200` com o dado alterado |
| `DELETE /api/<coisas>/1` | `204`; repetindo: `404` |

---

## Passo 5 — A tela (1h)

Copie [`web/index.html`](../web/index.html), [`web/app.js`](../web/app.js) e
[`web/style.css`](../web/style.css). A API já serve a pasta `web/` na raiz (última linha do
`main.py`).

O que adaptar no `index.html`: os campos do formulário e as colunas da tabela.
O que adaptar no `app.js`: o objeto `dados` no `submit`, a montagem da linha em
`carregarProdutos` e a função `editar`.

**Duas regras que se copiam:**

1. **Todo elemento que o teste vai tocar tem `data-cy`** (`input-<campo>`, `btn-salvar`,
   `btn-editar`, `btn-excluir`, `tabela-<coisas>`, `mensagem`). Cada linha da tabela recebe
   `data-cy="<coisa>-<identificador>"`.
2. **Todo texto vindo do usuário passa por `escapar(...)`** antes de ir para `innerHTML`
   (senão um nome como `<img src=x onerror=alert(1)>` executa código: XSS).

**Confira:** pela tela, crie, edite, exclua, e provoque um erro (cadastro repetido). A mensagem
de erro aparece em vermelho.

---

## Passo 6 — Testes unitários (1h)

### 6.1 Regras puras

Copie [`tests/unit/test_regras.py`](../api/tests/unit/test_regras.py) e reescreva para as
suas funções de `regras.py`. Para cada regra:

- **um caso válido**;
- **um caso inválido** com `pytest.raises(...)`;
- **valor-limite**: se a regra muda em 14 anos, teste **13, 14 e 15** com `@pytest.mark.parametrize`.

### 6.2 A API sem banco (dublê)

Copie [`tests/unit/test_api.py`](../api/tests/unit/test_api.py). O `FakeRepositorio` guarda
tudo num dicionário e tem **os mesmos métodos** do repositório real. A linha que faz a troca:

```python
app.dependency_overrides[get_repositorio] = lambda: repo
```

Adapte os campos em `novo(...)` e teste os códigos: 201, 404, 409, 422 e 204.

```bash
uv run pytest tests/unit -v
```

**Confira:** tudo verde, ao menos 5 testes, e ao menos um `parametrize` de valor-limite.

---

## Passo 7 — Teste de integração (30 min)

Copie [`tests/integracao/test_repositorio.py`](../api/tests/integracao/test_repositorio.py).
O fixture `repo` chama `resetar_dados(engine)` antes de cada teste. Escreva ao menos:

- um CRUD completo pelo repositório;
- um teste que prova que o **banco** recusa algo (UNIQUE, FK ou CHECK) com `pytest.raises(IntegrityError)`.

```bash
uv run pytest -m integracao -v                       # no SQLite
DATABASE_URL="mysql+pymysql://app:app@127.0.0.1:3306/<seu_banco>?charset=utf8mb4" \
  uv run pytest -m integracao -v                     # no MySQL
```

> No MySQL, violar um `CHECK` gera `OperationalError` (erro 3819), não `IntegrityError`.
> Use `pytest.raises(DBAPIError)`, que cobre os dois (é o que o modelo faz).

**Confira:** verde nos dois motores.

---

## Passo 8 — Cypress (1h30)

O guia completo, com cada comando explicado, está em **[CYPRESS.md](CYPRESS.md)**. O resumo:

```bash
cd e2e
npm init -y
npm install --save-dev cypress start-server-and-test
```

Copie do modelo:

| Arquivo | Adaptar |
|---|---|
| [`e2e/cypress.config.js`](../e2e/cypress.config.js) | `baseUrl`, se não for a porta 8000 |
| [`e2e/cypress/support/e2e.js`](../e2e/cypress/support/e2e.js) | nada |
| [`e2e/cypress/support/commands.js`](../e2e/cypress/support/commands.js) | `preencherProduto` → `preencher<Coisa>` com os seus campos |
| [`e2e/cypress/e2e/produtos.cy.js`](../e2e/cypress/e2e/produtos.cy.js) | renomeie para `<coisas>.cy.js` e reescreva com seus dados |
| scripts do [`e2e/package.json`](../e2e/package.json) | `cy:open`, `cy:run`, `e2e`, `api` |

Com a API rodando (`APP_ENV=test`) em outro terminal:

```bash
npm run cy:open
```

**Confira:** os testes de **READ, CREATE, UPDATE, DELETE** e **1 erro** verdes. Rode
`npm run cy:run` duas vezes seguidas: tem que passar **nas duas** (prova que o reset funciona).

---

## Passo 9 — CI no GitHub Actions (bônus, 30 min)

Copie [`.github/workflows/ci.yml`](../.github/workflows/ci.yml). Troque `estoque` pelo nome do
seu banco. Faça push.

**Confira:** na aba **Actions** do seu repositório, os três jobs verdes.

---

## Passo 10 — README e apresentação (30 min)

No `README.md` do seu projeto, no mínimo:

1. O que o sistema faz (2 linhas).
2. O modelo de dados (o desenho do Passo 3.1).
3. Como subir: os comandos do Passo 4.3.
4. Como rodar cada suíte: `uv run pytest`, `uv run pytest -m integracao`, `npm run cy:run`.

O roteiro da apresentação (10 min) e a rubrica estão no [INTENSIVO.md](../INTENSIVO.md#-a-apresentação-10-min-por-equipe).

---

## ✅ Checklist final antes de apresentar

- [ ] `docker compose up` (ou o comando sem Docker) sobe o sistema do zero
- [ ] Duas tabelas com FK; PK, UNIQUE e CHECK com nome
- [ ] Seed começa com `DELETE` e usa ids fixos
- [ ] SQL com parâmetros nomeados, nenhuma concatenação
- [ ] As 5 rotas respondem com os códigos certos
- [ ] A tela faz o CRUD completo e mostra erro em vermelho
- [ ] `uv run pytest tests/unit` verde, com valor-limite
- [ ] `uv run pytest -m integracao` verde
- [ ] `npm run cy:run` verde **duas vezes seguidas**
- [ ] README com os comandos
- [ ] (bônus) Actions verde
