"""Testes unitarios das regras de negocio (app/regras.py).

Funcao pura: nada de banco, nada de rede. Cada teste roda em milissegundos.
Padrao AAA: Arrange (prepara), Act (executa), Assert (confere).
"""

from decimal import Decimal

import pytest

from app.regras import (
    RegraVioladaError,
    normalizar_preco,
    normalizar_sku,
    status_estoque,
    valor_em_estoque,
)


class TestNormalizarSku:
    def test_aceita_sku_no_formato(self):
        assert normalizar_sku("ELE-001") == "ELE-001"

    def test_converte_para_maiusculas_e_tira_espacos(self):
        assert normalizar_sku("  pap-042 ") == "PAP-042"

    @pytest.mark.parametrize("invalido", ["", "EL-001", "ELE001", "ELE-01", "ELE-0001", "123-ABC"])
    def test_recusa_formato_invalido(self, invalido):
        with pytest.raises(RegraVioladaError, match="invalido"):
            normalizar_sku(invalido)


class TestStatusEstoque:
    # Analise de valor-limite: testamos exatamente nas bordas 0, 1, 5 e 6.
    @pytest.mark.parametrize(
        ("quantidade", "esperado"),
        [(0, "esgotado"), (1, "baixo"), (5, "baixo"), (6, "ok"), (1000, "ok")],
    )
    def test_classifica_pelas_faixas(self, quantidade, esperado):
        assert status_estoque(quantidade) == esperado

    def test_quantidade_negativa_e_erro(self):
        with pytest.raises(RegraVioladaError):
            status_estoque(-1)


class TestPreco:
    def test_arredonda_para_centavos(self):
        assert normalizar_preco(Decimal("10.005")) == Decimal("10.01")

    def test_recusa_preco_negativo(self):
        with pytest.raises(RegraVioladaError):
            normalizar_preco(Decimal("-0.01"))

    def test_valor_em_estoque_e_exato(self):
        # com float, 0.1 * 3 daria 0.30000000000000004
        assert valor_em_estoque(Decimal("0.10"), 3) == Decimal("0.30")

    def test_valor_em_estoque_zerado(self):
        assert valor_em_estoque(Decimal("99.90"), 0) == Decimal("0.00")
