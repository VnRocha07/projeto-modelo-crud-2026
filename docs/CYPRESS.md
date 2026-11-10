# 🌲 Cypress intensivo: do zero ao CRUD testado

Guia para ler junto com o código de [`e2e/`](../e2e/). Cada seção mostra **o conceito**, **o
código real do projeto modelo** e **o que você muda no seu projeto**.

> **Em uma frase:** o Cypress abre um navegador de verdade, clica e digita como um usuário,
> e confere se a tela mostra o que deveria. Se a API ou o banco estiverem errados, a tela
> mostra errado, e o teste pega.

---

## Sumário

1. [Onde o E2E entra na pirâmide](#1-onde-o-e2e-entra-na-pirâmide)
2. [Instalação](#2-instalação)
3. [A estrutura de pastas](#3-a-estrutura-de-pastas)
4. [O arquivo de configuração](#4-o-arquivo-de-configuração)
5. [Anatomia de um teste](#5-anatomia-de-um-teste)
6. [Encontrar elementos: seletores](#6-encontrar-elementos-seletores)
7. [Agir: digitar, clicar, escolher](#7-agir-digitar-clicar-escolher)
8. [Conferir: asserções](#8-conferir-asserções)
9. [A regra de ouro: o Cypress espera sozinho](#9-a-regra-de-ouro-o-cypress-espera-sozinho)
10. [Estado conhecido: resetar o banco antes de cada teste](#10-estado-conhecido-resetar-o-banco-antes-de-cada-teste)
11. [Comandos customizados](#11-comandos-customizados)
12. [Testar a API direto: `cy.request`](#12-testar-a-api-direto-cyrequest)
13. [Espiar e simular a rede: `cy.intercept`](#13-espiar-e-simular-a-rede-cyintercept)
14. [Janelas do navegador: `confirm` e `alert`](#14-janelas-do-navegador-confirm-e-alert)
15. [Rodando: `open`, `run`, um arquivo só](#15-rodando-open-run-um-arquivo-só)
16. [Cypress no GitHub Actions](#16-cypress-no-github-actions)
17. [Os 4 testes do CRUD, prontos para adaptar](#17-os-4-testes-do-crud-prontos-para-adaptar)
18. [Erros comuns](#18-erros-comuns)
19. [Exercícios](#19-exercícios)
20. [Cola rápida](#20-cola-rápida)

---

## 1. Onde o E2E entra na pirâmide

```
            /\
           /E2E\        poucos, lentos, pegam o sistema INTEIRO quebrado    <- Cypress
          /------\
         /integra-\     o SQL contra um banco de verdade                    <- pytest -m integracao
        /----------\
       /  unitário  \   muitos, rápidos, uma regra de cada vez              <- pytest tests/unit
      /--------------\
```

| Pergunta | Quem responde |
|---|---|
| "SKU `XX1` é inválido?" | **unitário** (`test_regras.py`): milissegundos, sem navegador |
| "O `JOIN` traz o nome da categoria?" | **integração** (`test_repositorio.py`) |
| "O usuário consegue cadastrar um produto pela tela e vê-lo na lista?" | **E2E** (`produtos.cy.js`) |

⚠️ **Erro comum:** testar cada regra pelo Cypress. Fica lento e frágil. No E2E, teste os
**fluxos do usuário** (as 4 operações do CRUD + 1 ou 2 erros). As regras vão no unitário.

---

## 2. Instalação

Pré-requisito: **Node 20 ou mais novo** (`node --version`).

No **seu** projeto, crie uma pasta só para os testes E2E:

```bash
mkdir e2e
cd e2e
npm init -y
npm install --save-dev cypress
```

O primeiro `npm install` baixa também o binário do Cypress (~ 500 MB). Demora na primeira vez.

Abra o Cypress pela primeira vez:

```bash
npx cypress open
```

Na janela que abre:

1. Escolha **E2E Testing**.
2. Clique em **Continue**: o Cypress cria `cypress.config.js` e a pasta `cypress/`.
3. Escolha um navegador (**Chrome** ou **Electron**) e **Start E2E Testing**.
4. **Create new spec** → ele cria um exemplo. Pode apagar depois.

Adicione atalhos no `package.json` (igual ao [do modelo](../e2e/package.json)):

```json
"scripts": {
  "cy:open": "cypress open",
  "cy:run": "cypress run"
}
```

> 💡 **Plano B sem instalar nada:** abra o repositório no **GitHub Codespaces**, rode
> `npm install` dentro de `e2e/` e use `npm run cy:run` (modo sem janela).

---

## 3. A estrutura de pastas

```
e2e/
├── package.json             dependências e atalhos (npm run ...)
├── cypress.config.js        configuração: endereço do sistema, pastas
└── cypress/
    ├── e2e/
    │   └── produtos.cy.js   OS TESTES. Todo arquivo .cy.js aqui é um "spec"
    ├── support/
    │   ├── e2e.js           roda antes de cada spec (importa os comandos)
    │   └── commands.js      seus comandos customizados (cy.dataCy, cy.resetarBanco)
    ├── fixtures/            (opcional) dados JSON para usar nos testes
    ├── screenshots/         gerado quando um teste falha (não versionar)
    └── videos/              gerado se video: true (não versionar)
```

No `.gitignore`:

```
node_modules/
e2e/cypress/screenshots/
e2e/cypress/videos/
```

---

## 4. O arquivo de configuração

[`e2e/cypress.config.js`](../e2e/cypress.config.js):

```js
const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: "http://localhost:8000",        // onde o SEU sistema roda
    specPattern: "cypress/e2e/**/*.cy.js",   // quais arquivos são testes
    supportFile: "cypress/support/e2e.js",
    video: false,                            // vídeo deixa lento; ligue se quiser
    screenshotOnRunFailure: true,            // print automático quando falha
    viewportWidth: 1280,
    viewportHeight: 900,
  },
});
```

**O que muda no seu projeto:** só o `baseUrl`. Se o seu front roda em outra porta
(ex.: React/Vite em `5173`), use essa.

Com `baseUrl` definido, `cy.visit("/")` vai para `http://localhost:8000/` e
`cy.request("/api/produtos")` vai para `http://localhost:8000/api/produtos`.

---

## 5. Anatomia de um teste

```js
describe("CRUD de produtos", () => {          // 1. agrupa testes relacionados

  beforeEach(() => {                          // 2. roda ANTES de cada it()
    cy.resetarBanco();
    cy.visit("/");
  });

  it("lista os produtos do seed (READ)", () => {  // 3. um teste = um comportamento
    cy.get('[data-cy="tabela-produtos"]')         // 4. ACHA o elemento
      .find("tr")                                 //    desce até as linhas
      .should("have.length", 5);                  // 5. CONFERE
  });
});
```

Todo teste E2E tem o mesmo formato de **três passos**:

```
ARRANGE   prepara o estado        cy.resetarBanco(); cy.visit("/")
ACT       faz o que o usuário faz cy.get(...).type(...); cy.get(...).click()
ASSERT    confere a tela          cy.get(...).should(...)
```

| Bloco | Para quê |
|---|---|
| `describe("...")` | agrupar (pode ter vários por arquivo) |
| `it("...")` | um teste. O texto deve dizer **o comportamento esperado** |
| `beforeEach` | preparar o estado antes de **cada** `it` |
| `before` | roda **uma vez** antes de todos (evite para estado de banco) |
| `afterEach` / `after` | limpeza (prefira limpar no `beforeEach`) |
| `it.only(...)` | roda **só** esse teste (útil ao depurar; **não** commite) |
| `it.skip(...)` | pula esse teste |

⚠️ Os comandos `cy.*` **não executam na hora**: eles entram numa fila e o Cypress executa em
ordem. Por isso **não** dá para fazer `const x = cy.get(...)` e usar `x` depois como um
elemento. Para pegar um valor, use `.then(...)` (ver seção 12).

---

## 6. Encontrar elementos: seletores

### O jeito certo: `data-cy`

No HTML ([`web/index.html`](../web/index.html)):

```html
<input id="sku" data-cy="input-sku" placeholder="ELE-003">
<button type="submit" data-cy="btn-salvar">Salvar</button>
<tbody id="tabela" data-cy="tabela-produtos"></tbody>
```

No teste:

```js
cy.get('[data-cy="input-sku"]')
```

**Por que `data-cy` e não `#id`, `.classe` ou o texto do botão?**

| Seletor | Problema |
|---|---|
| `.btn-primary` | o designer troca o CSS → o teste quebra sem o sistema ter quebrado |
| `#sku` | ids mudam em refatoração e às vezes se repetem |
| `contains("Salvar")` | alguém troca para "Gravar" → quebra |
| `div > div:nth-child(3) > button` | qualquer mudança de layout quebra |
| **`[data-cy="btn-salvar"]`** | existe **só** para o teste. Ninguém mexe sem saber |

**Regra para o seu projeto:** todo elemento que o teste vai **tocar ou conferir** ganha um
`data-cy`. Convenção sugerida:

```
input-<campo>     input-nome, input-preco
select-<campo>    select-categoria
btn-<acao>        btn-salvar, btn-editar, btn-excluir
tabela-<coisa>    tabela-produtos
mensagem          a área de sucesso/erro
```

### Linhas de tabela geradas pelo JavaScript

As linhas são criadas dinamicamente ([`web/app.js`](../web/app.js)). Damos a cada uma um
`data-cy` com o **identificador de negócio**:

```js
tr.dataset.cy = `produto-${p.sku}`;   // vira data-cy="produto-ELE-001"
```

E, dentro da linha, cada célula importante tem o seu:

```html
<td data-cy="nome">...</td>
<td data-cy="preco">...</td>
<button data-cy="btn-editar">Editar</button>
```

### Navegar entre elementos

```js
cy.get('[data-cy="tabela-produtos"]').find("tr")          // filhos que casam
cy.get('[data-cy="produto-ELE-001"]').within(() => {      // tudo dentro da linha
  cy.get('[data-cy="nome"]').should("have.text", "Mouse sem fio");
  cy.get('[data-cy="status"]').should("have.text", "ok");
});
cy.contains("tr", "Eletrônicos")                          // a <tr> que contém o texto
cy.get("tr").first()   /   .last()   /   .eq(2)           // por posição
```

`within` é o mais útil para tabelas: "dentro **desta** linha, ache o botão Editar".

### 🛠️ Descobrir o seletor sem adivinhar

No `cypress open`, clique no ícone de **mira** (Selector Playground) no topo do navegador e
clique no elemento: o Cypress mostra o `cy.get(...)` pronto, priorizando `data-cy`.

---

## 7. Agir: digitar, clicar, escolher

```js
cy.get('[data-cy="input-nome"]').type("Webcam HD");        // digita
cy.get('[data-cy="input-nome"]').clear().type("Outro");    // apaga e digita
cy.get('[data-cy="input-busca"]').type("caderno{enter}");  // tecla especial
cy.get('[data-cy="btn-salvar"]').click();                  // clica
cy.get('[data-cy="select-categoria"]').select("Eletrônicos"); // <select> pelo TEXTO
cy.get('[data-cy="select-categoria"]').select("1");        // ... ou pelo value
cy.get('[type="checkbox"]').check();  /  .uncheck();       // checkbox
cy.get('[data-cy="input-nome"]').focus().blur();           // foco
```

Teclas especiais dentro do `type`: `{enter}`, `{esc}`, `{backspace}`, `{selectall}`,
`{downArrow}`.

⚠️ **Campo de edição já preenchido:** use **sempre** `.clear()` antes de `.type()`. Senão
o texto novo é **somado** ao antigo ("Café 500 gCafé 1 kg").

---

## 8. Conferir: asserções

O `should` é o coração do teste:

```js
.should("have.text", "Mouse sem fio")   // texto EXATO
.should("contain", "199,90")            // contém o texto
.should("have.value", "Café 500 g")     // valor de <input>
.should("have.length", 5)               // quantidade de elementos
.should("be.visible")                   // está visível
.should("not.exist")                    // sumiu do DOM (ex.: depois de excluir)
.should("exist")
.should("have.class", "erro")           // tem a classe CSS
.should("be.disabled")  /  "be.enabled"
.should("have.attr", "href", "/x")
```

Encadeie com `and`:

```js
cy.get('[data-cy="mensagem"]')
  .should("have.class", "erro")
  .and("contain", "ja cadastrado");
```

Negação: prefixe com `not.` → `"not.have.class"`, `"not.contain"`, `"not.be.visible"`.

Quando você já tem o valor (dentro de um `.then`), use `expect`:

```js
cy.request("/api/produtos").then((resposta) => {
  expect(resposta.status).to.eq(200);
  expect(resposta.body).to.have.length(5);
});
```

### `have.text` x `contain`

`have.text` exige o texto inteiro. A célula de preço mostra `R$ 199,90` (e o espaço depois do
`R$` é um caractere especial, não um espaço comum). Por isso o modelo usa
`should("contain", "199,90")`.

---

## 9. A regra de ouro: o Cypress espera sozinho

Depois de clicar em **Salvar**, a tela demora alguns milissegundos: o JavaScript chama a
API, a API grava no banco, a tabela é redesenhada. Você **não** precisa esperar:

```js
cy.get('[data-cy="btn-salvar"]').click();
cy.get('[data-cy="tabela-produtos"]').find("tr").should("have.length", 6);
```

O `should` **tenta de novo** por até **4 segundos** até a condição ficar verdadeira. Se nunca
ficar, o teste falha mostrando o que encontrou. Isso se chama *retry-ability*.

🚫 **Nunca faça:**

```js
cy.get('[data-cy="btn-salvar"]').click();
cy.wait(3000);                // espera fixa: lento quando sobra, falha quando falta
```

✅ **Espere pelo que importa:** uma asserção sobre a tela (acima) ou a resposta da rede
(seção 13, `cy.wait("@alias")`).

Se uma operação realmente demora mais de 4 s:

```js
cy.get('[data-cy="relatorio"]', { timeout: 10000 }).should("be.visible");
```

---

## 10. Estado conhecido: resetar o banco antes de cada teste

**O problema:** o teste "cria ELE-003" passa na primeira vez. Na segunda, o ELE-003 já existe,
a API devolve 409, e o teste falha. Pior: o teste "lista 5 produtos" passa sozinho, mas falha
quando roda depois do teste de criação (agora são 6).

**A regra:** cada `it` começa do **mesmo estado**, e nenhum depende de outro.

**A solução do modelo:** uma rota que devolve o banco ao seed, **existindo só em ambiente de
teste**. Em [`api/app/main.py`](../api/app/main.py):

```python
if os.getenv("APP_ENV") == "test":
    # NUNCA habilite em producao: ela apaga todos os dados.
    @app.post("/api/_test/reset", status_code=204)
    def resetar(request: Request):
        resetar_dados(request.app.state.engine)   # executa db/seed.sql
        return Response(status_code=204)
```

O [`db/seed.sql`](../db/seed.sql) começa com `DELETE` e depois `INSERT` com **ids fixos**, por
isso pode ser executado quantas vezes for preciso.

No teste:

```js
beforeEach(() => {
  cy.request("POST", "/api/_test/reset");   // banco volta ao seed
  cy.visit("/");                            // tela recarregada
});
```

E existe um **teste unitário** garantindo que a rota não existe fora do ambiente de teste
([`test_api.py`](../api/tests/unit/test_api.py), `test_rota_de_reset_nao_existe_fora_do_ambiente_de_teste`).

**Para o seu projeto (Flask):**

```python
if os.getenv("APP_ENV") == "test":
    @app.post("/api/_test/reset")
    def resetar():
        executar_sql("db/seed.sql")
        return "", 204
```

> Alternativa sem rota: `cy.exec("docker compose exec -T db mysql -uapp -papp estoque < ../db/seed.sql")`.
> Funciona, mas depende do Docker na máquina de quem roda o teste.

---

## 11. Comandos customizados

Repetir `cy.get('[data-cy="..."]')` cansa e polui o teste. Em
[`cypress/support/commands.js`](../e2e/cypress/support/commands.js):

```js
Cypress.Commands.add("dataCy", (valor) => cy.get(`[data-cy="${valor}"]`));

Cypress.Commands.add("resetarBanco", () => {
  cy.request("POST", "/api/_test/reset").its("status").should("eq", 204);
});

Cypress.Commands.add("preencherProduto", ({ sku, nome, preco, quantidade, categoria }) => {
  if (sku !== undefined) cy.dataCy("input-sku").clear().type(sku);
  if (nome !== undefined) cy.dataCy("input-nome").clear().type(nome);
  if (preco !== undefined) cy.dataCy("input-preco").clear().type(preco);
  if (quantidade !== undefined) cy.dataCy("input-quantidade").clear().type(quantidade);
  if (categoria !== undefined) cy.dataCy("select-categoria").select(categoria);
});

Cypress.Commands.add("linhaDoProduto", (sku) => cy.dataCy(`produto-${sku}`));
```

O [`support/e2e.js`](../e2e/cypress/support/e2e.js) importa esse arquivo, e a partir daí
todo spec pode usar `cy.dataCy(...)`, `cy.resetarBanco()`, etc.

Resultado: o teste lê como uma história.

```js
cy.preencherProduto({ sku: "ele-003", nome: "Webcam HD", preco: "199.90", quantidade: "4" });
cy.dataCy("btn-salvar").click();
cy.linhaDoProduto("ELE-003").should("exist");
```

---

## 12. Testar a API direto: `cy.request`

`cy.request` faz uma chamada HTTP **sem passar pela tela**. Serve para:

- preparar dados rápido (criar 3 produtos antes de testar a busca);
- testar a API em si.

```js
it("faz o ciclo completo via cy.request", () => {
  const produto = { sku: "PAP-777", nome: "Grampeador", preco: "15.50", quantidade: 9, categoria_id: 2 };

  cy.request("POST", "/api/produtos", produto).then(({ status, body }) => {
    expect(status).to.eq(201);
    expect(body).to.include({ sku: "PAP-777", categoria: "Papelaria", status: "ok" });

    cy.request("PUT", `/api/produtos/${body.id}`, { ...produto, quantidade: 2 })
      .its("body.status").should("eq", "baixo");

    cy.request("DELETE", `/api/produtos/${body.id}`).its("status").should("eq", 204);

    cy.request({ url: `/api/produtos/${body.id}`, failOnStatusCode: false })
      .its("status").should("eq", 404);
  });
});
```

Pontos importantes:

- `.then((resposta) => ...)` é como você **pega um valor** (o `id` criado) para usar depois.
- `.its("body.status")` extrai um campo e permite `should` em cima dele.
- Por padrão, `cy.request` **falha o teste** se a resposta for 4xx/5xx. Para testar um 404 de
  propósito, passe `failOnStatusCode: false`.

---

## 13. Espiar e simular a rede: `cy.intercept`

`cy.intercept` fica no meio do caminho entre a tela e a API. Dois usos:

### a) Esperar a requisição certa (em vez de `cy.wait(ms)`)

```js
cy.intercept("POST", "/api/produtos").as("criar");   // 1. define ANTES da ação
cy.dataCy("btn-salvar").click();                     // 2. ação
cy.wait("@criar").its("response.statusCode").should("eq", 201);  // 3. espera e confere
```

Isso prova que a tela **chamou a API certa** e que a API respondeu 201.

### b) Simular uma resposta (testar o que a API não faz sob demanda)

Como testar a mensagem de erro quando o servidor cai? Não dá para derrubar o servidor no meio
do teste, mas dá para **fingir**:

```js
cy.intercept("POST", "/api/produtos", {
  statusCode: 500,
  body: { detail: "falha simulada no servidor" },
}).as("criar");

cy.preencherProduto({ sku: "ELE-050", nome: "Qualquer", preco: "1", quantidade: "1" });
cy.dataCy("btn-salvar").click();
cy.wait("@criar");
cy.dataCy("mensagem").should("have.class", "erro").and("contain", "falha simulada");
```

Os dois exemplos estão no spec do modelo, no `describe("Rede (cy.intercept)")`.

⚠️ Com resposta simulada, **a API real não é chamada**: nada é gravado no banco. Use para
testar a **tela**, não a API.

---

## 14. Janelas do navegador: `confirm` e `alert`

O botão Excluir do modelo pergunta "Excluir o produto X?" com `confirm()`. O Cypress
**aceita automaticamente** todo `confirm`. Para conferir o texto ou **cancelar**:

```js
// conferir o texto e aceitar
cy.on("window:confirm", (texto) => {
  expect(texto).to.contain("Caneta azul");
  return true;              // true = OK
});

// cancelar
cy.on("window:confirm", () => false);
```

Para `alert`: `cy.on("window:alert", (texto) => expect(texto).to.eq("Salvo!"))`.

⚠️ O `cy.on(...)` vem **antes** do `click` que abre a janela.

---

## 15. Rodando: `open`, `run`, um arquivo só

A API (ou o seu sistema) precisa estar **rodando antes**, com `APP_ENV=test`.

**Terminal 1** (o sistema):

```bash
cd api
APP_ENV=test uv run uvicorn app.main:app --reload
```

**Terminal 2** (os testes):

```bash
cd e2e
npm run cy:open       # com janela: escolhe o spec e vê cada passo
npm run cy:run        # sem janela: roda tudo e imprime o resumo (o que o CI faz)
```

Outras formas úteis:

```bash
npx cypress run --spec cypress/e2e/produtos.cy.js   # um arquivo só
npx cypress run --browser chrome                    # outro navegador
npx cypress run --headed                            # run, mas mostrando a janela
```

**Tudo num comando só** (o modelo já tem): `npm run e2e`. Ele usa o pacote
`start-server-and-test` para subir a API, esperar `/api/saude` responder, rodar o Cypress
e desligar a API no final.

### Lendo o `cypress open`

```
┌───────────────────────────┬─────────────────────────────────────┐
│ COMMAND LOG               │                                     │
│  1 request POST /api/...  │        o seu sistema, ao vivo       │
│  2 visit /                │                                     │
│  3 get [data-cy=...]      │                                     │
│  4 - assert expected ...  │                                     │
└───────────────────────────┴─────────────────────────────────────┘
```

- **Clique num passo** do log: a tela à direita volta **no tempo** para aquele momento
  (*time travel*). É assim que se descobre por que um teste falhou.
- Salvou o arquivo de teste? O Cypress **roda de novo sozinho**.
- Passo vermelho: leia a mensagem. Ela diz o que esperava e o que encontrou.

### Quando falha no `cypress run`

O Cypress tira um print automático em `e2e/cypress/screenshots/`. No CI do modelo, esses prints
viram um **artefato** para download na aba Actions.

---

## 16. Cypress no GitHub Actions

Trecho do [`ci.yml`](../.github/workflows/ci.yml) do modelo:

```yaml
  e2e:
    runs-on: ubuntu-latest
    services:
      mysql:                       # banco de verdade, só para o CI
        image: mysql:8.4
        # ...
    env:
      APP_ENV: test                # habilita o reset
    steps:
      - uses: actions/checkout@v4
      # ... espera o MySQL, carrega esquema e seed, instala a API ...
      - run: npm install
        working-directory: e2e
      - uses: cypress-io/github-action@v6
        with:
          working-directory: e2e
          install: false
          start: uv run --directory ../api uvicorn app.main:app --port 8000
          wait-on: http://localhost:8000/api/saude
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: cypress-screenshots
          path: e2e/cypress/screenshots
```

A action oficial faz o mesmo que o `npm run e2e`: `start` sobe o sistema, `wait-on` espera
ficar de pé, e então roda `cypress run`.

---

## 17. Os 4 testes do CRUD, prontos para adaptar

Copie, troque os `data-cy` e os dados pelo seu domínio. É o mínimo exigido no intensivão.

```js
describe("CRUD de <entidade>", () => {
  beforeEach(() => {
    cy.resetarBanco();
    cy.visit("/");
  });

  it("lista os registros do seed (READ)", () => {
    cy.dataCy("tabela-<entidade>").find("tr").should("have.length", /* qtd do seed */ 5);
  });

  it("cria um registro (CREATE)", () => {
    cy.dataCy("input-nome").type("Novo registro");
    // ... os outros campos
    cy.dataCy("btn-salvar").click();
    cy.dataCy("mensagem").should("contain", "criado");
    cy.dataCy("tabela-<entidade>").should("contain", "Novo registro");
  });

  it("edita um registro (UPDATE)", () => {
    cy.dataCy("<entidade>-1").find('[data-cy="btn-editar"]').click();
    cy.dataCy("input-nome").clear().type("Nome alterado");
    cy.dataCy("btn-salvar").click();
    cy.dataCy("<entidade>-1").should("contain", "Nome alterado");
  });

  it("exclui um registro (DELETE)", () => {
    cy.dataCy("<entidade>-1").find('[data-cy="btn-excluir"]').click();
    cy.dataCy("<entidade>-1").should("not.exist");
  });

  it("mostra erro ao salvar dado inválido", () => {
    cy.dataCy("btn-salvar").click();            // formulário vazio
    cy.dataCy("mensagem").should("have.class", "erro");
  });
});
```

---

## 18. Erros comuns

| O que aparece | Causa | Correção |
|---|---|---|
| `Cypress could not verify that this server is running: http://localhost:8000` | o sistema não está de pé | suba a API antes (Terminal 1) ou use `npm run e2e` |
| `cy.request() failed ... 404 Not Found` em `/api/_test/reset` | API sem `APP_ENV=test` | suba com `APP_ENV=test` |
| `Timed out retrying after 4000ms: Expected to find element: [data-cy="..."], but never found it` | `data-cy` digitado errado, ou o elemento não existe nessa tela | confira no HTML; use o Selector Playground |
| `expected '<td>' to have text 'R$ 199,90', but the text was 'R$ 199,90'` | espaço especial na formatação de moeda | use `contain` com o trecho numérico |
| texto do campo sai duplicado | `type` sem `clear` num campo já preenchido | `.clear().type(...)` |
| `cy.type() failed because it requires a valid typeable element` | `type` num `<div>` ou `<select>` | `type` só em `input`/`textarea`; `<select>` usa `.select()` |
| passa sozinho, falha junto com os outros | um teste depende do estado deixado pelo anterior | reset no `beforeEach` |
| passa na 1ª vez, falha na 2ª | o dado criado ficou no banco | reset no `beforeEach` |
| passa às vezes, falha às vezes | `cy.wait(ms)` ou asserção antes da tela atualizar | troque por `should` ou `cy.wait("@alias")` |
| `cy.get(...).then is not a function` / valor `undefined` | tentou usar `cy.get` como variável | use `.then((el) => ...)` |
| `npm ERR! ... ETIMEDOUT` no `npm install` | rede da faculdade bloqueando o npm | roteie pelo celular ou use o Codespaces |

---

## 19. Exercícios

Faça **no projeto modelo** primeiro, depois repita no seu.

1. **Aquecimento.** Rode `npm run cy:open`, abra `produtos.cy.js` e clique em cada passo do
   teste "edita um produto" para ver o *time travel*.
2. **Quebre de propósito.** Em `web/index.html`, troque `data-cy="btn-salvar"` por
   `data-cy="btn-gravar"`. Rode os testes e leia a mensagem de erro. Desfaça.
3. **Quebre a API.** Em `api/app/regras.py`, troque `LIMITE_ESTOQUE_BAIXO = 5` por `10`. Quais
   testes falham: unitário, E2E, ou os dois? Por quê? Desfaça.
4. **Novo teste.** Escreva um `it` que cria um produto com quantidade `0` e confere que o status
   na tabela é `esgotado`.
5. **Cancelar edição.** Escreva um `it` que clica em Editar, depois em **Cancelar edição**, e
   confere que o título volta a ser "Novo produto" e o campo SKU fica vazio.
6. **Intercept.** Escreva um `it` que simula `GET /api/produtos` devolvendo `[]` e confere que
   a mensagem "Nenhum produto encontrado." aparece.
7. **No seu projeto.** Os 4 testes do CRUD + 1 de erro (seção 17), verdes.

---

## 20. Cola rápida

```js
// estrutura
describe("...", () => { beforeEach(() => {...}); it("...", () => {...}); });

// navegar
cy.visit("/")

// achar
cy.get('[data-cy="x"]')     cy.dataCy("x")      cy.contains("tr", "texto")
.find("tr")   .first()   .eq(2)   .within(() => {...})

// agir
.type("abc")   .clear()   .click()   .select("Opção")   .check()   .type("{enter}")

// conferir
.should("have.text", "...")   .should("contain", "...")   .should("have.value", "...")
.should("have.length", 3)     .should("be.visible")       .should("not.exist")
.should("have.class", "erro") .and("contain", "...")

// API
cy.request("POST", "/api/x", corpo).then(({ status, body }) => expect(status).to.eq(201))
cy.request({ url: "/api/x/99", failOnStatusCode: false }).its("status").should("eq", 404)

// rede
cy.intercept("POST", "/api/x").as("salvar");   ...   cy.wait("@salvar")
cy.intercept("GET", "/api/x", { statusCode: 500, body: {...} })

// janelas
cy.on("window:confirm", () => true)

// rodar
npm run cy:open     npm run cy:run     npx cypress run --spec caminho.cy.js
```
