// Testes E2E do CRUD de produtos: navegador de verdade, API de verdade, banco de verdade.
// Cada teste comeca do seed (5 produtos), entao a ordem de execucao nao importa.

describe("CRUD de produtos", () => {
  beforeEach(() => {
    cy.resetarBanco();
    cy.visit("/");
  });

  it("lista os produtos do seed (READ)", () => {
    cy.dataCy("tabela-produtos").find("tr").should("have.length", 5);
    cy.linhaDoProduto("ELE-001").within(() => {
      cy.dataCy("nome").should("have.text", "Mouse sem fio");
      cy.dataCy("status").should("have.text", "ok");
    });
    cy.linhaDoProduto("PAP-002").find('[data-cy="status"]').should("have.text", "esgotado");
  });

  it("cria um produto novo (CREATE)", () => {
    cy.preencherProduto({
      sku: "ele-003", // minusculo de proposito: a API normaliza
      nome: "Webcam HD",
      preco: "199.90",
      quantidade: "4",
      categoria: "Eletrônicos",
    });
    cy.dataCy("btn-salvar").click();

    cy.dataCy("mensagem").should("contain", "Produto ELE-003 criado");
    cy.dataCy("tabela-produtos").find("tr").should("have.length", 6);
    cy.linhaDoProduto("ELE-003").within(() => {
      cy.dataCy("nome").should("have.text", "Webcam HD");
      cy.dataCy("preco").should("contain", "199,90");
      cy.dataCy("status").should("have.text", "baixo");
    });
  });

  it("edita um produto existente (UPDATE)", () => {
    cy.linhaDoProduto("ALI-001").find('[data-cy="btn-editar"]').click();
    cy.dataCy("titulo-form").should("have.text", "Editando ALI-001");
    cy.dataCy("input-nome").should("have.value", "Café 500 g");

    cy.preencherProduto({ nome: "Café 1 kg", preco: "45.00", quantidade: "0" });
    cy.dataCy("btn-salvar").click();

    cy.dataCy("mensagem").should("contain", "Produto ALI-001 atualizado");
    cy.dataCy("titulo-form").should("have.text", "Novo produto");
    cy.linhaDoProduto("ALI-001").within(() => {
      cy.dataCy("nome").should("have.text", "Café 1 kg");
      cy.dataCy("status").should("have.text", "esgotado");
    });
  });

  it("exclui um produto (DELETE)", () => {
    cy.on("window:confirm", (texto) => {
      expect(texto).to.contain("Caneta azul");
      return true;
    });
    cy.linhaDoProduto("PAP-002").find('[data-cy="btn-excluir"]').click();

    cy.dataCy("mensagem").should("contain", "Produto PAP-002 excluído");
    cy.linhaDoProduto("PAP-002").should("not.exist");
    cy.dataCy("tabela-produtos").find("tr").should("have.length", 4);
  });

  it("nao exclui quando o usuario cancela a confirmacao", () => {
    cy.on("window:confirm", () => false);
    cy.linhaDoProduto("PAP-002").find('[data-cy="btn-excluir"]').click();
    cy.linhaDoProduto("PAP-002").should("exist");
  });

  it("busca por nome e por SKU", () => {
    cy.dataCy("input-busca").type("caderno");
    cy.dataCy("tabela-produtos").find("tr").should("have.length", 1);
    cy.linhaDoProduto("PAP-001").should("exist");

    cy.dataCy("input-busca").clear().type("ele-");
    cy.dataCy("tabela-produtos").find("tr").should("have.length", 2);

    cy.dataCy("input-busca").clear().type("nao-existe");
    cy.dataCy("lista-vazia").should("be.visible");
  });
});

describe("Validacoes e erros", () => {
  beforeEach(() => {
    cy.resetarBanco();
    cy.visit("/");
  });

  it("recusa SKU duplicado (409 vindo do banco/API)", () => {
    cy.preencherProduto({ sku: "ELE-001", nome: "Mouse repetido", preco: "10", quantidade: "1" });
    cy.dataCy("btn-salvar").click();
    cy.dataCy("mensagem").should("have.class", "erro").and("contain", "ja cadastrado");
    cy.dataCy("tabela-produtos").find("tr").should("have.length", 5);
  });

  it("recusa SKU fora do formato (422)", () => {
    cy.preencherProduto({ sku: "XX1", nome: "Invalido", preco: "10", quantidade: "1" });
    cy.dataCy("btn-salvar").click();
    cy.dataCy("mensagem").should("have.class", "erro").and("contain", "sku");
  });

  it("mostra o resumo por categoria calculado no SQL (GROUP BY)", () => {
    cy.dataCy("tabela-resumo").contains("tr", "Eletrônicos").should("contain", "2.005,80");
  });
});

describe("API (sem interface)", () => {
  beforeEach(() => cy.resetarBanco());

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
});
