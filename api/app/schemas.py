"""Contratos de entrada e saida da API (validados pelo Pydantic)."""

from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.regras import normalizar_preco, normalizar_sku


class ProdutoEntrada(BaseModel):
    sku: str = Field(examples=["ELE-003"])
    nome: str = Field(min_length=2, max_length=120)
    preco: Decimal = Field(ge=0, max_digits=10, decimal_places=2)
    quantidade: int = Field(ge=0)
    categoria_id: int

    @field_validator("sku")
    @classmethod
    def _sku(cls, valor: str) -> str:
        return normalizar_sku(valor)

    @field_validator("nome")
    @classmethod
    def _nome(cls, valor: str) -> str:
        valor = valor.strip()
        if len(valor) < 2:
            raise ValueError("nome precisa ter ao menos 2 caracteres")
        return valor

    @field_validator("preco")
    @classmethod
    def _preco(cls, valor: Decimal) -> Decimal:
        return normalizar_preco(valor)


class Produto(BaseModel):
    id: int
    sku: str
    nome: str
    preco: Decimal
    quantidade: int
    categoria_id: int
    categoria: str
    status: str


class Categoria(BaseModel):
    id: int
    nome: str


class ResumoCategoria(BaseModel):
    categoria: str
    produtos: int
    unidades: int
    valor_total: Decimal
