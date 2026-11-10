"""Testes unitarios da camada HTTP (app/main.py), SEM banco.

O repositorio real e trocado por um dublê em memoria (FakeRepositorio) usando
app.dependency_overrides. Assim testamos so as regras da API: codigos de status,
validacao de entrada, 404, 409 e 422.
"""

from decimal import Decimal

import pytest
from fastapi.testclient import TestClient

from app.main import app, get_repositorio
from app.regras import status_estoque
from app.schemas import Categoria, Produto


class FakeRepositorio:
    """Implementa os mesmos metodos do RepositorioProdutos, guardando em um dict."""

    def __init__(self):
        self.categorias = {1: "Eletrônicos"}
        self.produtos: dict[int, Produto] = {}
        self.proximo_id = 1

    def _montar(self, pid, dados) -> Produto:
        return Produto(
            id=pid, **dados.model_dump(),
            categoria=self.categorias[dados.categoria_id],
            status=status_estoque(dados.quantidade),
        )

    def listar(self, busca=None):
        itens = list(self.produtos.values())
        if busca:
            itens = [p for p in itens if busca.lower() in p.nome.lower()]
        return itens

    def buscar(self, pid):
        return self.produtos.get(pid)

    def sku_em_uso(self, sku, ignorar_id=None):
        return any(p.sku == sku and p.id != ignorar_id for p in self.produtos.values())

    def categoria_existe(self, cid):
        return cid in self.categorias

    def listar_categorias(self):
        return [Categoria(id=i, nome=n) for i, n in self.categorias.items()]

    def criar(self, dados):
        produto = self._montar(self.proximo_id, dados)
        self.produtos[produto.id] = produto
        self.proximo_id += 1
        return produto

    def atualizar(self, pid, dados):
        self.produtos[pid] = self._montar(pid, dados)
        return self.produtos[pid]

    def remover(self, pid):
        return self.produtos.pop(pid, None) is not None


@pytest.fixture
def repo():
    return FakeRepositorio()


@pytest.fixture
def cliente(repo):
    app.dependency_overrides[get_repositorio] = lambda: repo
    yield TestClient(app)
    app.dependency_overrides.clear()


def novo(**alteracoes):
    base = {"sku": "ELE-010", "nome": "Fone", "preco": "99.90", "quantidade": 4, "categoria_id": 1}
    return {**base, **alteracoes}


def test_saude(cliente):
    assert cliente.get("/api/saude").json() == {"status": "ok"}


def test_criar_devolve_201_e_normaliza_sku(cliente):
    resposta = cliente.post("/api/produtos", json=novo(sku=" ele-010 "))
    assert resposta.status_code == 201
    corpo = resposta.json()
    assert corpo["sku"] == "ELE-010"
    assert corpo["status"] == "baixo"
    assert Decimal(corpo["preco"]) == Decimal("99.90")


def test_criar_com_sku_repetido_devolve_409(cliente):
    cliente.post("/api/produtos", json=novo())
    resposta = cliente.post("/api/produtos", json=novo(nome="Outro"))
    assert resposta.status_code == 409


def test_criar_com_categoria_inexistente_devolve_422(cliente):
    resposta = cliente.post("/api/produtos", json=novo(categoria_id=99))
    assert resposta.status_code == 422
    assert "categoria 99" in resposta.json()["detail"]


@pytest.mark.parametrize(
    "campo_invalido",
    [{"sku": "X"}, {"nome": " "}, {"preco": "-1"}, {"quantidade": -1}, {"preco": "abc"}],
)
def test_entrada_invalida_devolve_422(cliente, campo_invalido):
    assert cliente.post("/api/produtos", json=novo(**campo_invalido)).status_code == 422


def test_obter_inexistente_devolve_404(cliente):
    assert cliente.get("/api/produtos/123").status_code == 404


def test_atualizar(cliente):
    pid = cliente.post("/api/produtos", json=novo()).json()["id"]
    resposta = cliente.put(f"/api/produtos/{pid}", json=novo(quantidade=0))
    assert resposta.status_code == 200
    assert resposta.json()["status"] == "esgotado"


def test_atualizar_mantendo_o_proprio_sku_nao_e_conflito(cliente):
    pid = cliente.post("/api/produtos", json=novo()).json()["id"]
    assert cliente.put(f"/api/produtos/{pid}", json=novo(nome="Fone 2")).status_code == 200


def test_atualizar_inexistente_devolve_404(cliente):
    assert cliente.put("/api/produtos/9", json=novo()).status_code == 404


def test_remover(cliente, repo):
    pid = cliente.post("/api/produtos", json=novo()).json()["id"]
    assert cliente.delete(f"/api/produtos/{pid}").status_code == 204
    assert repo.produtos == {}
    assert cliente.delete(f"/api/produtos/{pid}").status_code == 404


def test_rota_de_reset_nao_existe_fora_do_ambiente_de_teste(cliente):
    # APP_ENV nao e "test" aqui; a rota perigosa nao pode estar exposta
    assert cliente.post("/api/_test/reset").status_code in (404, 405)
