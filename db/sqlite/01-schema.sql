-- Mesmo esquema do db/mysql/01-schema.sql, no dialeto do SQLite.
-- Usado para rodar a API e os testes sem Docker.
-- A API liga PRAGMA foreign_keys = ON em toda conexao (app/db.py).

CREATE TABLE IF NOT EXISTS categoria (
    id    INTEGER      PRIMARY KEY AUTOINCREMENT,
    nome  VARCHAR(60)  NOT NULL,
    CONSTRAINT uq_categoria_nome UNIQUE (nome)
);

CREATE TABLE IF NOT EXISTS produto (
    id            INTEGER        PRIMARY KEY AUTOINCREMENT,
    sku           VARCHAR(20)    NOT NULL,
    nome          VARCHAR(120)   NOT NULL,
    preco         DECIMAL(10, 2) NOT NULL,
    quantidade    INTEGER        NOT NULL DEFAULT 0,
    categoria_id  INTEGER        NOT NULL,
    criado_em     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_produto_sku UNIQUE (sku),
    CONSTRAINT ck_produto_preco CHECK (preco >= 0),
    CONSTRAINT ck_produto_quantidade CHECK (quantidade >= 0),
    CONSTRAINT fk_produto_categoria FOREIGN KEY (categoria_id)
        REFERENCES categoria (id)
        ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS ix_produto_nome ON produto (nome);
