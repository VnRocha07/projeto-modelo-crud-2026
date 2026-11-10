"""Acesso a dados com SQL escrito a mao.

Cada metodo e uma consulta que o aluno de Banco de Dados reconhece:
SELECT com JOIN, INSERT, UPDATE, DELETE e um GROUP BY no resumo.
Os parametros sao sempre nomeados (:sku), nunca concatenados na string:
e isso que impede SQL injection.
"""

from decimal import Decimal

from sqlalchemy import Engine, text

from app.regras import status_estoque
from app.schemas import Categoria, Produto, ProdutoEntrada, ResumoCategoria

SELECT_PRODUTO = """
    SELECT p.id, p.sku, p.nome, p.preco, p.quantidade,
           p.categoria_id, c.nome AS categoria
      FROM produto p
      JOIN categoria c ON c.id = p.categoria_id
"""


def _para_produto(linha) -> Produto:
    dados = dict(linha._mapping)
    # o SQLite devolve DECIMAL como float; normalizamos para Decimal com 2 casas
    dados["preco"] = Decimal(str(dados["preco"])).quantize(Decimal("0.01"))
    dados["status"] = status_estoque(dados["quantidade"])
    return Produto(**dados)


def _parametros(dados: ProdutoEntrada) -> dict:
    # o driver do SQLite nao aceita Decimal; texto ('79.90') e exato nos dois motores
    return {**dados.model_dump(), "preco": str(dados.preco)}


class RepositorioProdutos:
    def __init__(self, engine: Engine):
        self.engine = engine

    # ---------- leitura ----------

    def listar(self, busca: str | None = None) -> list[Produto]:
        sql = SELECT_PRODUTO
        params = {}
        if busca:
            sql += " WHERE LOWER(p.nome) LIKE :busca OR LOWER(p.sku) LIKE :busca"
            params["busca"] = f"%{busca.lower()}%"
        sql += " ORDER BY p.nome"
        with self.engine.connect() as conn:
            return [_para_produto(l) for l in conn.execute(text(sql), params)]

    def buscar(self, produto_id: int) -> Produto | None:
        with self.engine.connect() as conn:
            linha = conn.execute(
                text(SELECT_PRODUTO + " WHERE p.id = :id"), {"id": produto_id}
            ).first()
        return _para_produto(linha) if linha else None

    def sku_em_uso(self, sku: str, ignorar_id: int | None = None) -> bool:
        with self.engine.connect() as conn:
            linha = conn.execute(
                text("SELECT id FROM produto WHERE sku = :sku"), {"sku": sku}
            ).first()
        return linha is not None and linha.id != ignorar_id

    def categoria_existe(self, categoria_id: int) -> bool:
        with self.engine.connect() as conn:
            return conn.execute(
                text("SELECT 1 FROM categoria WHERE id = :id"), {"id": categoria_id}
            ).first() is not None

    def listar_categorias(self) -> list[Categoria]:
        with self.engine.connect() as conn:
            linhas = conn.execute(text("SELECT id, nome FROM categoria ORDER BY nome"))
            return [Categoria(**dict(l._mapping)) for l in linhas]

    def resumo(self) -> list[ResumoCategoria]:
        sql = """
            SELECT c.nome AS categoria,
                   COUNT(p.id) AS produtos,
                   COALESCE(SUM(p.quantidade), 0) AS unidades,
                   COALESCE(SUM(p.preco * p.quantidade), 0) AS valor_total
              FROM categoria c
              LEFT JOIN produto p ON p.categoria_id = c.id
             GROUP BY c.id, c.nome
             ORDER BY c.nome
        """
        with self.engine.connect() as conn:
            resultado = []
            for linha in conn.execute(text(sql)):
                dados = dict(linha._mapping)
                dados["valor_total"] = Decimal(str(dados["valor_total"])).quantize(
                    Decimal("0.01")
                )
                resultado.append(ResumoCategoria(**dados))
            return resultado

    # ---------- escrita ----------

    def criar(self, dados: ProdutoEntrada) -> Produto:
        with self.engine.begin() as conn:
            resultado = conn.execute(
                text("""
                    INSERT INTO produto (sku, nome, preco, quantidade, categoria_id)
                    VALUES (:sku, :nome, :preco, :quantidade, :categoria_id)
                """),
                _parametros(dados),
            )
            novo_id = resultado.lastrowid
        return self.buscar(novo_id)

    def atualizar(self, produto_id: int, dados: ProdutoEntrada) -> Produto | None:
        with self.engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE produto
                       SET sku = :sku, nome = :nome, preco = :preco,
                           quantidade = :quantidade, categoria_id = :categoria_id
                     WHERE id = :id
                """),
                {**_parametros(dados), "id": produto_id},
            )
        return self.buscar(produto_id)

    def remover(self, produto_id: int) -> bool:
        with self.engine.begin() as conn:
            resultado = conn.execute(
                text("DELETE FROM produto WHERE id = :id"), {"id": produto_id}
            )
        return resultado.rowcount > 0
