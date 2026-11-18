# 🪟 Como rodar no Windows (VS Code) — do pytest ao MySQL

Guia para a atividade do professor: **rodar o projeto, mostrar o pytest e demonstrar o
exercício** (`DELETE /api/categorias/{id}`). Aqui os comandos estão no formato do
**terminal do VS Code no Windows** (PowerShell).

O pytest completo roda **sem Docker** (SQLite). O Docker/MySQL é necessário só para as
seções **9 a 13** (seed, restrições, API no MySQL e a demonstração do exercício).
Node e Cypress não são precisos: o E2E está fora do escopo pedido.

> O `docs/PASSO-A-PASSO.md` usa sintaxe bash (`APP_ENV=test comando`). No PowerShell isso
> não funciona; a versão equivalente está neste guia.

**Caminho mínimo (só pytest):** itens 1 a 6.
**Caminho completo (pytest + exercício no MySQL):** itens 1 a 12 (o 13 é opcional).

---

## ✅ O que já está pronto neste computador

| Item | Situação |
|---|---|
| `uv` | instalado (versão 0.12.x) |
| Python | 3.13.15, gerenciado pelo `uv` (já baixado) |
| Dependências do `api/` | instaladas em `api/.venv` com `uv sync` (35 pacotes) |
| pytest | 9.2.0 + pytest-cov 7.1.0 + httpx 0.28.1 |
| Banco dos testes | SQLite (o `pytest` cria um temporário sozinho) |
| Docker Desktop + MySQL 8.4 | opcional; sobe pela seção 9 (`docker compose up -d db`) |

O `.venv` e o `.pytest_cache` já estão no `.gitignore`: não sujam o `git status`.

---

## 🚀 Passo a passo (copie e cole, um bloco por vez)

### 1) Abrir o projeto e o terminal

- No VS Code: **File → Open Folder…** → escolha `projeto-modelo-crud-2026`.
- **Terminal → New Terminal** (o terminal abre em PowerShell).
- Confira o `uv`:

```powershell
uv --version
```

Esperado: algo como `uv 0.12.9`.

### 2) Entrar na pasta da API

Todos os comandos de pytest rodam **dentro de `api/`** (é lá que está o `pyproject.toml`
com `pythonpath = ["."]`; na raiz o pytest não acha o pacote `app`).

```powershell
cd api
```

### 3) Instalar/confirmar as dependências

```powershell
uv sync
```

Esperado (já está tudo instalado, então é rapidinho):

```text
Resolved 37 packages in 4ms
Checked 35 packages in 28ms
```

Se algum dia a `.venv` quebrar, use `uv sync --reinstall`.

### 4) Rodar a suíte completa (**é o que o professor pede**)

```powershell
uv run pytest -q
```

Esperado: a última linha é exatamente esta:

```text
48 passed in 3.21s
```

(48 testes = 36 unitários + 12 de integração. O tempo pode variar.)

### 5) Mostrar os unitários, um por um

```powershell
uv run pytest tests/unit -v
```

Esperado: `36 passed`. Repare nos casos de **valor-limite** do estoque
(`0 → esgotado`, `1 → baixo`, `5 → baixo`, `6 → ok`) e no `parametrize` de SKU inválido:
é o "valor-limite" que o Passo 6.1 do guide do professor cobra.

### 6) Mostrar os testes de integração (SQL de verdade no SQLite)

```powershell
uv run pytest -m integracao -v
```

Esperado: `12 passed, 36 deselected`. Aqui aparecem UNIQUE, FK, CHECK, JOIN e GROUP BY
sendo exercitados no banco — inclusive o teste do **exercício** (`DELETE /api/categorias/{id}`)
com o banco de verdade.

### 7) (Opcional, se quiser impressionar) Cobertura

```powershell
uv run pytest --cov
```

Mostra a tabela de cobertura de `app/` (usa o `pytest-cov`, já instalado). O total fica em
torno de **90%**, acima do mínimo de 80% exigido no CI.

### 8) (Opcional) Subir a API e ver a tela (SQLite)

```powershell
$env:APP_ENV = "test"
uv run uvicorn app.main:app --reload
```

- Tela do estoque: <http://localhost:8000>
- Documentação interativa: <http://localhost:8000/docs>
- Para parar: `Ctrl+C` no terminal.
- Na primeira subida ele cria `api/estoque.db` (o seed do banco; está no `.gitignore`).
- `$env:APP_ENV = "test"` é o equivalente PowerShell de `APP_ENV=test`; a rota
  `POST /api/_test/reset` só existe com essa variável. Em um terminal novo ela some
  sozinha (e há um teste unitário que garante isso).

---

## 🐬 MySQL no Docker (para o exercício valer ponto)

### 9) Subir o banco e conferir o seed

Na **raiz do projeto** (não em `api/`):

```powershell
docker compose up -d db
```

Esperado: o container `projeto-modelo-crud-2026-db-1` sobe e fica `healthy`.

```powershell
docker compose ps
```

Confira as tabelas e o seed:

```powershell
docker compose exec db mysql -uapp -papp --default-character-set=utf8mb4 estoque -e "SHOW TABLES"
docker compose exec db mysql -uapp -papp --default-character-set=utf8mb4 estoque -e "SELECT id, nome FROM categoria"
docker compose exec db mysql -uapp -papp --default-character-set=utf8mb4 estoque -e "SELECT id, sku, nome, preco, quantidade, categoria_id FROM produto"
```

Esperado: as tabelas `categoria` e `produto`, 3 categorias e **5 produtos** com ids fixos.
(O aviso `Using a password on the command line interface can be insecure.` é normal do MySQL.)

Para entrar no banco de forma interativa:

```powershell
docker compose exec db mysql -uapp -papp --default-character-set=utf8mb4 estoque
```

### 10) Provar que cada restrição funciona (violando de propósito)

Rode um comando por vez e mostre o **erro** na tela. Cada um viola uma restrição diferente:

```powershell
# PK (ERROR 1062: Duplicate entry '1' for key 'categoria.PRIMARY')
docker compose exec db mysql -uapp -papp estoque -e "INSERT INTO categoria (id, nome) VALUES (1, 'Repetida')"

# UNIQUE do SKU (ERROR 1062: Duplicate entry 'ELE-001' ... uq_produto_sku)
docker compose exec db mysql -uapp -papp estoque -e "INSERT INTO produto (sku, nome, preco, quantidade, categoria_id) VALUES ('ELE-001', 'Repetido', 10.00, 1, 1)"

# CHECK de preço (ERROR 3819: Check constraint 'ck_produto_preco' is violated)
docker compose exec db mysql -uapp -papp estoque -e "INSERT INTO produto (sku, nome, preco, quantidade, categoria_id) VALUES ('CHK-001', 'Preco negativo', -1.00, 1, 1)"

# CHECK de quantidade (ERROR 3819: ck_produto_quantidade)
docker compose exec db mysql -uapp -papp estoque -e "INSERT INTO produto (sku, nome, preco, quantidade, categoria_id) VALUES ('CHK-002', 'Qtd negativa', 10.00, -1, 1)"

# FK: categoria inexistente (ERROR 1452: fk_produto_categoria)
docker compose exec db mysql -uapp -papp estoque -e "INSERT INTO produto (sku, nome, preco, quantidade, categoria_id) VALUES ('CHK-003', 'Sem categoria', 10.00, 1, 999)"

# FK ON DELETE RESTRICT: apagar categoria em uso (ERROR 1451)
docker compose exec db mysql -uapp -papp estoque -e "DELETE FROM categoria WHERE id = 1"
```

Esperado: **PK 1062**, **UNIQUE 1062**, **CHECK 3819** (duas vezes), **FK 1452** e
**FK RESTRICT 1451**. Se o erro 2002 (socket) aparecer, o MySQL ainda está iniciando:
espere alguns segundos e rode de novo.

> Os scripts de criação só rodam na **primeira** subida (volume vazio). Se precisar recriar
> o banco do zero: `docker compose down -v` e depois `docker compose up -d db`.

### 11) Subir a API apontando para o MySQL

Ainda na **raiz**, abra a pasta `api` e configure as duas variáveis:

```powershell
cd api
$env:APP_ENV = "test"
$env:DATABASE_URL = "mysql+pymysql://app:app@127.0.0.1:3306/estoque?charset=utf8mb4"
uv run uvicorn app.main:app --reload
```

- Tela: <http://localhost:8000> — confira no `SELECT`/na tela que os dados são os do MySQL.
- Swagger: <http://localhost:8000/docs>.
- Para parar: `Ctrl+C`. Em um terminal novo as variáveis `$env:` somem sozinhas.
- A variável `DATABASE_URL` é **quem decide o banco** (`api/app/db.py`): sem ela, a API usa
  o SQLite (`api/estoque.db`).

> Alternativa que sobe banco + API juntos (sem `uv` no terminal):
> `docker compose up --build` na raiz. A API fica em <http://localhost:8000>.

### 12) Demonstrar o exercício com curl (204 / 404 / 409)

Com a API rodando (seção 11), abra **outro terminal** (não precisa ser dentro de `api/`).

> ⚠️ No PowerShell, `curl` é apelido de `Invoke-WebRequest`. Use **`curl.exe`** para ter o
> `curl` de verdade.

```powershell
# 409 — a categoria 1 (Eletrônicos) ainda tem produtos
curl.exe -s -X DELETE http://localhost:8000/api/categorias/1 -w "\nstatus: %{http_code}\n"
# -> {"detail":"categoria em uso"}
#    status: 409

# 404 — categoria que não existe
curl.exe -s -X DELETE http://localhost:8000/api/categorias/999 -w "\nstatus: %{http_code}\n"
# -> {"detail":"categoria nao encontrada"}
#    status: 404

# 204 — para apagar de verdade, primeiro esvazie a categoria 3
# (o produto 5, ALI-001, é o único dela)
curl.exe -s -X DELETE http://localhost:8000/api/produtos/5 -w "\nstatus: %{http_code}\n"
curl.exe -s -X DELETE http://localhost:8000/api/categorias/3 -w "\nstatus: %{http_code}\n"
# -> status: 204  (corpo vazio)

# 404 — apagar a mesma categoria de novo
curl.exe -s -X DELETE http://localhost:8000/api/categorias/3 -w "\nstatus: %{http_code}\n"

# Restaura o seed para deixar o banco como estava
curl.exe -s -X POST http://localhost:8000/api/_test/reset -w "\nstatus: %{http_code}\n"
# -> status: 204
```

**Por que o 409 sai de graça:** a rota não conta produtos antes. Ela tenta o `DELETE`; a FK
`fk_produto_categoria` com `ON DELETE RESTRICT` faz o banco recusar, o SQLAlchemy levanta
`IntegrityError` e a rota devolve **409** (veja `api/app/main.py` e
`api/app/repositorio.py`).

### 13) (Opcional) Rodar a integração do pytest no MySQL

Com o banco da seção 9 de pé e ainda dentro de `api/`:

```powershell
$env:DATABASE_URL = "mysql+pymysql://app:app@127.0.0.1:3306/estoque?charset=utf8mb4"
uv run pytest -m integracao -v
# -> 12 passed, 36 deselected
Remove-Item Env:DATABASE_URL
```

Aqui o mesmo SQL roda no MySQL em vez do SQLite (inclusive o teste do exercício).

### Parar tudo no fim

```powershell
# na raiz do projeto:
docker compose stop db     # para o banco, mantendo os dados
docker compose down        # remove o container, mantendo o volume
docker compose down -v     # remove também os dados (próxima subida recria e reseeda)
```

E `Ctrl+C` no terminal da API (seção 11) para desligá-la.

---

## 📋 Checkpoints do `docs/PASSO-A-PASSO.md`

| Checkpoint do guia | Como conferir | Resultado aqui |
|---|---|---|
| Passo 1: `uv run pytest -q` | comando do item 4 | **48 passed** ✅ |
| Passo 1: a API responde na tela e no `/docs` | comando do item 8 | **200** na tela e no `/docs` ✅ |
| Passo 3: Docker sobe o banco e o seed aparece | seção 9 | 2 tabelas, 3 categorias, 5 produtos ✅ |
| Passo 3.4: provar cada restrição violando | seção 10 | PK 1062, UNIQUE 1062, CHECK 3819, FK 1452, FK RESTRICT 1451 ✅ |
| Passo 4.3: as 5 rotas com os códigos certos | `/docs` + testes unitários | 201/200/204/404/409/422 cobertos ✅ |
| Exercício: `DELETE /api/categorias/{id}` | seção 12 (curl) + pytest | 204/404/409 provados no MySQL ✅ |
| Passo 6: unitários verdes, com `parametrize` de valor-limite | `pytest tests/unit -v` | **36 passed** ✅ |
| Passo 7: integração verde no SQLite | `pytest -m integracao -v` | **12 passed** ✅ |
| Passo 7 no MySQL (Docker) | seção 13 | **12 passed** ✅ |
| Seed começa com `DELETE` e usa ids fixos | `db/seed.sql` | ✅ |
| SQL com parâmetros nomeados (sem concatenação) | `api/app/repositorio.py` | ✅ |
| Rota de reset só com `APP_ENV=test` | `api/app/main.py` | ✅ |
| PK, UNIQUE, CHECK e FK com nome | `db/mysql/01-schema.sql` / `db/sqlite/01-schema.sql` | ✅ |
| Passo 8 (Cypress) e Passo 9 (CI) | — | fora do escopo pedido: **E2E ignorado** |

---

## 🧯 Se algo der errado

| Sintoma | Causa provável | Solução |
|---|---|---|
| `uv : não é reconhecido...` | terminal aberto antes da instalação | feche e abra o terminal do VS Code de novo; confira `uv --version` |
| `ModuleNotFoundError: No module named 'app'` | rodou o pytest na raiz | entre em `api` (`cd api`) antes de rodar |
| `pytest: no tests ran` | pasta errada | idem: `cd api` |
| Quer recriar o ambiente | `.venv` corrompida | `uv sync --reinstall` |
| `APP_ENV=test` não funciona | sintaxe bash no PowerShell | use `$env:APP_ENV = "test"` |
| `docker: ... cannot connect` ou `permission denied` | Docker Desktop fechado/iniciando | abra o Docker Desktop e espere "engine running" |
| `Bind for 127.0.0.1:3306 failed` | já existe outro MySQL na porta | pare o outro ou `docker compose down` antes |
| `Bind for 127.0.0.1:8000 failed` | já tem API rodando | `Ctrl+C` no outro terminal da API |
| `ERROR 2002 ... socket` no mysql | MySQL ainda inicializando | espere o `docker compose ps` ficar `healthy` e rode de novo |
| `ERROR 1045 (access denied)` | usuário/senha errados | use `-uapp -papp` (e `estoque` no fim) |
| Aviso `Using a password on the command line interface...` | normal do MySQL 8.4 | pode ignorar |
| `curl` mostra um objeto estranho / erro | no PowerShell `curl` é alias | use **`curl.exe`** |
| Acentos errados no banco/tela | cliente sem utf8mb4 | use `--default-character-set=utf8mb4` no mysql |

---

## 🎤 Roteiro curto para apresentar

1. `cd api`
2. `uv sync` (mostra que o ambiente é reprodutível)
3. `uv run pytest -q` → **48 passed**
4. `uv run pytest tests/unit -v` → destaque do `parametrize` de valor-limite
5. `uv run pytest -m integracao -v` → destaque do UNIQUE/FK/CHECK no banco
6. (Opcional) suba a API e abra `/docs` para mostrar as rotas
7. (Diferencial) seção 9: `docker compose up -d db`, `SHOW TABLES` e o seed no `SELECT`
8. (Diferencial) seção 10: violar PK/UNIQUE/CHECK/FK e mostrar os erros
9. (**Exercício vale ponto**) seção 12:
   - `curl.exe -X DELETE localhost:8000/api/categorias/1` → **409**
   - `.../categorias/999` → **404**
   - esvaziar a categoria 3 e apagar → **204**
