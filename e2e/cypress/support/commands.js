// Comandos customizados: deixam os testes legiveis e evitam repeticao.

// Seleciona pelo atributo data-cy. Seletor estavel: nao quebra se mudar CSS ou texto.
Cypress.Commands.add("dataCy", (valor) => cy.get(`[data-cy="${valor}"]`));

// Volta o banco ao estado do seed (rota so existe com APP_ENV=test).
Cypress.Commands.add("resetarBanco", () => {
  cy.request("POST", "/api/_test/reset").its("status").should("eq", 204);
});

// Preenche o formulario de produto. Campos omitidos ficam como estao.
Cypress.Commands.add("preencherProduto", ({ sku, nome, preco, quantidade, categoria }) => {
  if (sku !== undefined) cy.dataCy("input-sku").clear().type(sku);
  if (nome !== undefined) cy.dataCy("input-nome").clear().type(nome);
  if (preco !== undefined) cy.dataCy("input-preco").clear().type(preco);
  if (quantidade !== undefined) cy.dataCy("input-quantidade").clear().type(quantidade);
  if (categoria !== undefined) cy.dataCy("select-categoria").select(categoria);
});

Cypress.Commands.add("linhaDoProduto", (sku) => cy.dataCy(`produto-${sku}`));
