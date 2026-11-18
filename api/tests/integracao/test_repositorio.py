"""Testes de integracao: o SQL de verdade contra um banco de verdade.

Por padrao usam um SQLite temporario. Para rodar no MySQL:
    DATABASE_URL=mysql+pymysql://app:app@localhost:3306/estoque uv run pytest -m integracao

Aqui aparecem coisas que o teste unitario NAO pega: restricao UNIQUE, chave
estrangeira, CHECK, JOIN e GROUP BY.
"""

import os
from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError

from app.db import criar_engine, preparar_banco, resetar_dados
from app.main import app, get_repositorio
from app.repositorio import RepositorioProdutos
from app.schemas import ProdutoEntrada

pytestmark = pytest.mark.integracao


@pytest.fixture(scope="module")
def engine(tmp_path_factory):
    url = os.getenv("DATABASE_URL") or f"sqlite:///{tmp_path_factory.mktemp('db')}/teste.db"
    engine = criar_engine(url)
    preparar_banco(engine)
    yield engine
    engine.dispose()


@pytest.fixture
def repo(engine):
    resetar_dados(engine)  # cada teste parte do seed
    return RepositorioProdutos(engine)


def entrada(**alteracoes):
    base = {"sku": "ELE-099", "nome": "Monitor", "preco": "899.00", "quantidade": 2, "categoria_id": 1}
    return ProdutoEntrada(**{**base, **alteracoes})


def test_seed_carregado(repo):
    assert len(repo.listar()) == 5
    assert [c.nome for c in repo.listar_categorias()] == ["Alimentos", "Eletrônicos", "Papelaria"]


def test_listar_faz_join_com_categoria(repo):
    mouse = repo.buscar(1)
    assert mouse.categoria == "Eletrônicos"
    assert mouse.preco == Decimal("79.90")


def test_busca_por_nome_e_por_sku(repo):
    assert [p.sku for p in repo.listar("caderno")] == ["PAP-001"]
    assert {p.sku for p in repo.listar("ele-")} == {"ELE-001", "ELE-002"}


def test_crud_completo(repo):
    criado = repo.criar(entrada())
    assert criado.id is not None
    assert repo.buscar(criado.id).nome == "Monitor"

    atualizado = repo.atualizar(criado.id, entrada(nome="Monitor 27", quantidade=0))
    assert (atualizado.nome, atualizado.status) == ("Monitor 27", "esgotado")

    assert repo.remover(criado.id) is True
    assert repo.buscar(criado.id) is None
    assert repo.remover(criado.id) is False


def test_preco_decimal_nao_perde_centavos(repo):
    criado = repo.criar(entrada(preco="0.10", quantidade=3))
    assert criado.preco == Decimal("0.10")


def test_banco_recusa_sku_duplicado(repo):
    # a API checa antes, mas o banco e a ultima linha de defesa
    with pytest.raises(IntegrityError):
        repo.criar(entrada(sku="ELE-001"))


def test_banco_recusa_categoria_inexistente(repo):
    with pytest.raises(IntegrityError):
        repo.criar(entrada(categoria_id=999))


def test_banco_recusa_quantidade_negativa(engine, repo):
    # CHECK violado: o SQLite levanta IntegrityError, o MySQL (erro 3819) OperationalError.
    # Os dois herdam de DBAPIError.
    with pytest.raises(DBAPIError, match="(?i)check"), engine.begin() as conn:
        conn.execute(text("UPDATE produto SET quantidade = -1 WHERE id = 1"))


def test_banco_impede_apagar_categoria_em_uso(engine, repo):
    with pytest.raises(IntegrityError), engine.begin() as conn:
        conn.execute(text("DELETE FROM categoria WHERE id = 1"))


# ---------- exercicio: DELETE /api/categorias/{id} ----------


def test_repositorio_recusa_apagar_categoria_em_uso(repo):
    # o repositorio tenta o DELETE direto, sem contar produtos antes;
    # a FK ON DELETE RESTRICT recusa e o IntegrityError sobe
    with pytest.raises(IntegrityError):
        repo.remover_categoria(1)
    assert repo.categoria_existe(1) is True


def test_rota_delete_categoria_com_banco_de_verdade(engine, repo):
    """204, 404 e 409 com o banco de verdade: o 409 vem do IntegrityError da FK."""
    app.dependency_overrides[get_repositorio] = lambda: repo
    try:
        # sem "with": nao roda o lifespan, para nao criar um segundo banco
        cliente = TestClient(app)
        # categoria 1 (Eletronicos) ainda tem produtos no seed -> o banco recusa
        assert cliente.delete("/api/categorias/1").status_code == 409
        # categoria que nao existe
        assert cliente.delete("/api/categorias/999").status_code == 404
        # uma categoria sem produtos pode ser apagada
        with engine.begin() as conn:
            conn.execute(text("INSERT INTO categoria (id, nome) VALUES (99, 'Vazia')"))
        assert cliente.delete("/api/categorias/99").status_code == 204
        assert repo.categoria_existe(99) is False
    finally:
        app.dependency_overrides.clear()


def test_resumo_agrupa_por_categoria(repo):
    resumo = {r.categoria: r for r in repo.resumo()}
    eletronicos = resumo["Eletrônicos"]
    assert (eletronicos.produtos, eletronicos.unidades) == (2, 15)
    # 79.90 * 12 + 349.00 * 3
    assert eletronicos.valor_total == Decimal("2005.80")
