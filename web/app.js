// Front-end sem framework: fetch na API e manipulacao do DOM.
// Os atributos data-cy no HTML sao os "ganchos" que o Cypress usa para achar os elementos.

const API = "/api";
const $ = (id) => document.getElementById(id);
// Todo texto vindo do usuario passa por aqui antes de ir para innerHTML (evita XSS).
const escapar = (v) => String(v).replace(/[&<>"']/g, (c) =>
  ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);
const moeda = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

async function chamar(caminho, opcoes = {}) {
  const resposta = await fetch(API + caminho, {
    headers: { "Content-Type": "application/json" },
    ...opcoes,
  });
  if (resposta.status === 204) return null;
  const corpo = await resposta.json();
  if (!resposta.ok) {
    // 422 do FastAPI vem como lista; 404/409 como texto
    const detalhe = Array.isArray(corpo.detail)
      ? corpo.detail.map((e) => `${e.loc.at(-1)}: ${e.msg}`).join("; ")
      : corpo.detail;
    throw new Error(detalhe);
  }
  return corpo;
}

function mostrarMensagem(texto, tipo = "sucesso") {
  const el = $("mensagem");
  el.textContent = texto;
  el.className = tipo;
}

async function carregarCategorias() {
  const categorias = await chamar("/categorias");
  $("categoria").innerHTML = categorias
    .map((c) => `<option value="${c.id}">${escapar(c.nome)}</option>`)
    .join("");
}

async function carregarProdutos() {
  const busca = $("busca").value.trim();
  const produtos = await chamar("/produtos" + (busca ? `?busca=${encodeURIComponent(busca)}` : ""));
  $("vazio").hidden = produtos.length > 0;
  $("tabela").innerHTML = "";
  for (const p of produtos) {
    const tr = document.createElement("tr");
    tr.dataset.cy = `produto-${p.sku}`; // dataset nao interpreta HTML
    tr.innerHTML = `
      <td>${escapar(p.sku)}</td>
      <td data-cy="nome">${escapar(p.nome)}</td>
      <td>${escapar(p.categoria)}</td>
      <td data-cy="preco">${moeda.format(p.preco)}</td>
      <td data-cy="quantidade">${p.quantidade}</td>
      <td><span class="status ${p.status}" data-cy="status">${p.status}</span></td>
      <td class="acoes-linha">
        <button class="secundario" data-cy="btn-editar">Editar</button>
        <button class="perigo" data-cy="btn-excluir">Excluir</button>
      </td>`;
    tr.querySelector('[data-cy="btn-editar"]').onclick = () => editar(p);
    tr.querySelector('[data-cy="btn-excluir"]').onclick = () => excluir(p);
    $("tabela").appendChild(tr);
  }
}

async function carregarResumo() {
  const linhas = await chamar("/resumo");
  $("resumo").innerHTML = linhas
    .map((r) => `<tr><td>${escapar(r.categoria)}</td><td>${r.produtos}</td><td>${r.unidades}</td>
                 <td>${moeda.format(r.valor_total)}</td></tr>`)
    .join("");
}

async function recarregar() {
  await Promise.all([carregarProdutos(), carregarResumo()]);
}

function limparFormulario() {
  $("form-produto").reset();
  $("produto-id").value = "";
  $("titulo-form").textContent = "Novo produto";
  $("btn-cancelar").hidden = true;
}

function editar(p) {
  $("produto-id").value = p.id;
  $("sku").value = p.sku;
  $("nome").value = p.nome;
  $("preco").value = p.preco;
  $("quantidade").value = p.quantidade;
  $("categoria").value = p.categoria_id;
  $("titulo-form").textContent = `Editando ${p.sku}`;
  $("btn-cancelar").hidden = false;
  mostrarMensagem("");
}

async function excluir(p) {
  if (!confirm(`Excluir o produto ${p.nome}?`)) return;
  try {
    await chamar(`/produtos/${p.id}`, { method: "DELETE" });
    mostrarMensagem(`Produto ${p.sku} excluído.`);
    if ($("produto-id").value == p.id) limparFormulario();
    await recarregar();
  } catch (erro) {
    mostrarMensagem(erro.message, "erro");
  }
}

$("form-produto").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const id = $("produto-id").value;
  const dados = {
    sku: $("sku").value,
    nome: $("nome").value,
    preco: $("preco").value,
    quantidade: Number($("quantidade").value),
    categoria_id: Number($("categoria").value),
  };
  try {
    const salvo = await chamar(id ? `/produtos/${id}` : "/produtos", {
      method: id ? "PUT" : "POST",
      body: JSON.stringify(dados),
    });
    mostrarMensagem(id ? `Produto ${salvo.sku} atualizado.` : `Produto ${salvo.sku} criado.`);
    limparFormulario();
    await recarregar();
  } catch (erro) {
    mostrarMensagem(erro.message, "erro");
  }
});

$("btn-cancelar").addEventListener("click", () => {
  limparFormulario();
  mostrarMensagem("");
});

let espera;
$("busca").addEventListener("input", () => {
  clearTimeout(espera);
  espera = setTimeout(carregarProdutos, 250);
});

carregarCategorias().then(recarregar);
