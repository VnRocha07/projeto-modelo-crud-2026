"""Conexao com o banco.

A URL vem da variavel DATABASE_URL:
  mysql+pymysql://app:app@localhost:3306/estoque   (Docker, o motor da disciplina)
  sqlite:///./estoque.db                          (padrao, roda sem Docker)
"""

import os
from pathlib import Path

from sqlalchemy import Engine, create_engine, event, text

RAIZ = Path(__file__).resolve().parents[2]
PASTA_DB = RAIZ / "db"
URL_PADRAO = "sqlite:///./estoque.db"


def criar_engine(url: str | None = None) -> Engine:
    url = url or os.getenv("DATABASE_URL", URL_PADRAO)
    if url.startswith("sqlite"):
        engine = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def _ligar_fk(conexao_dbapi, _registro):
            # o SQLite vem com chave estrangeira DESLIGADA por padrao
            conexao_dbapi.execute("PRAGMA foreign_keys = ON")

        return engine
    return create_engine(url, pool_pre_ping=True)


def executar_arquivo_sql(engine: Engine, caminho: Path) -> None:
    """Executa um .sql comando a comando (separados por ';')."""
    sem_comentarios = "\n".join(
        linha for linha in caminho.read_text(encoding="utf-8").splitlines()
        if not linha.strip().startswith("--")
    )
    comandos = [c.strip() for c in sem_comentarios.split(";") if c.strip()]
    with engine.begin() as conn:
        for comando in comandos:
            conn.execute(text(comando))


def preparar_banco(engine: Engine) -> None:
    """No SQLite, cria o esquema e carrega o seed se o banco estiver vazio.

    No MySQL quem faz isso e o proprio conteiner (docker-compose.yml).
    """
    if engine.dialect.name != "sqlite":
        return
    executar_arquivo_sql(engine, PASTA_DB / "sqlite" / "01-schema.sql")
    with engine.connect() as conn:
        vazio = conn.execute(text("SELECT COUNT(*) FROM categoria")).scalar_one() == 0
    if vazio:
        resetar_dados(engine)


def resetar_dados(engine: Engine) -> None:
    """Volta o banco para o estado do seed. Usado pelos testes."""
    executar_arquivo_sql(engine, PASTA_DB / "seed.sql")
