"""Regras de negocio puras: sem banco, sem HTTP.

Por serem funcoes puras, sao o alvo ideal de teste unitario
(tests/unit/test_regras.py): entrada -> saida, nada mais.
"""

import re
from decimal import ROUND_HALF_UP, Decimal

PADRAO_SKU = re.compile(r"^[A-Z]{3}-\d{3}$")
LIMITE_ESTOQUE_BAIXO = 5


class RegraVioladaError(ValueError):
    """Dado que nao respeita uma regra de negocio."""


def normalizar_sku(sku: str) -> str:
    """Remove espacos, poe em maiusculas e valida o formato AAA-000."""
    normalizado = sku.strip().upper()
    if not PADRAO_SKU.match(normalizado):
        raise RegraVioladaError(
            f"SKU '{sku}' invalido: use 3 letras, hifen e 3 digitos (ex.: ELE-001)"
        )
    return normalizado


def normalizar_preco(preco: Decimal) -> Decimal:
    """Arredonda para centavos e recusa valor negativo."""
    if preco < 0:
        raise RegraVioladaError("preco nao pode ser negativo")
    return preco.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def status_estoque(quantidade: int) -> str:
    """Classifica o estoque: 'esgotado' (0), 'baixo' (1 a 5) ou 'ok' (mais de 5)."""
    if quantidade < 0:
        raise RegraVioladaError("quantidade nao pode ser negativa")
    if quantidade == 0:
        return "esgotado"
    if quantidade <= LIMITE_ESTOQUE_BAIXO:
        return "baixo"
    return "ok"


def valor_em_estoque(preco: Decimal, quantidade: int) -> Decimal:
    """Quanto dinheiro esta parado na prateleira para um produto."""
    return normalizar_preco(preco) * quantidade
