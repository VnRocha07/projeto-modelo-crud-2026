"""API REST do estoque + servidor do front-end (pasta web/).

Rotas:
  GET    /api/saude
  GET    /api/categorias
  GET    /api/produtos?busca=
  GET    /api/produtos/{id}
  POST   /api/produtos
  PUT    /api/produtos/{id}
  DELETE /api/produtos/{id}
  GET    /api/resumo
  POST   /api/_test/reset      (so existe com APP_ENV=test)

Documentacao interativa: http://localhost:8000/docs
"""

import os
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, Request, Response, status
from fastapi.staticfiles import StaticFiles

from app.db import RAIZ, criar_engine, preparar_banco, resetar_dados
from app.repositorio import RepositorioProdutos
from app.schemas import Categoria, Produto, ProdutoEntrada, ResumoCategoria


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    engine = criar_engine()
    preparar_banco(engine)
    app.state.engine = engine
    yield
    engine.dispose()


app = FastAPI(title="Estoque - projeto modelo", version="1.0.0", lifespan=ciclo_de_vida)


def get_repositorio(request: Request) -> RepositorioProdutos:
    """Injecao de dependencia: os testes unitarios trocam isto por um dublê."""
    return RepositorioProdutos(request.app.state.engine)


def _validar_referencias(repo, dados: ProdutoEntrada, produto_id: int | None = None):
    if not repo.categoria_existe(dados.categoria_id):
        raise HTTPException(422, detail=f"categoria {dados.categoria_id} nao existe")
    if repo.sku_em_uso(dados.sku, ignorar_id=produto_id):
        raise HTTPException(409, detail=f"SKU {dados.sku} ja cadastrado")


@app.get("/api/saude")
def saude():
    return {"status": "ok"}


@app.get("/api/categorias", response_model=list[Categoria])
def listar_categorias(repo=Depends(get_repositorio)):
    return repo.listar_categorias()


@app.get("/api/produtos", response_model=list[Produto])
def listar_produtos(busca: str | None = None, repo=Depends(get_repositorio)):
    return repo.listar(busca)


@app.get("/api/produtos/{produto_id}", response_model=Produto)
def obter_produto(produto_id: int, repo=Depends(get_repositorio)):
    produto = repo.buscar(produto_id)
    if produto is None:
        raise HTTPException(404, detail="produto nao encontrado")
    return produto


@app.post("/api/produtos", response_model=Produto, status_code=status.HTTP_201_CREATED)
def criar_produto(dados: ProdutoEntrada, repo=Depends(get_repositorio)):
    _validar_referencias(repo, dados)
    return repo.criar(dados)


@app.put("/api/produtos/{produto_id}", response_model=Produto)
def atualizar_produto(produto_id: int, dados: ProdutoEntrada, repo=Depends(get_repositorio)):
    if repo.buscar(produto_id) is None:
        raise HTTPException(404, detail="produto nao encontrado")
    _validar_referencias(repo, dados, produto_id)
    return repo.atualizar(produto_id, dados)


@app.delete("/api/produtos/{produto_id}", status_code=status.HTTP_204_NO_CONTENT)
def remover_produto(produto_id: int, repo=Depends(get_repositorio)):
    if not repo.remover(produto_id):
        raise HTTPException(404, detail="produto nao encontrado")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@app.get("/api/resumo", response_model=list[ResumoCategoria])
def resumo(repo=Depends(get_repositorio)):
    return repo.resumo()


if os.getenv("APP_ENV") == "test":
    # Rota de apoio aos testes E2E: devolve o banco ao estado do seed.
    # NUNCA habilite em producao: ela apaga todos os dados.
    @app.post("/api/_test/reset", status_code=status.HTTP_204_NO_CONTENT)
    def resetar(request: Request):
        resetar_dados(request.app.state.engine)
        return Response(status_code=status.HTTP_204_NO_CONTENT)


# Por ultimo: o front-end estatico na raiz. Vem depois das rotas /api.
app.mount("/", StaticFiles(directory=RAIZ / "web", html=True), name="web")
