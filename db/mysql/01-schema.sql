-- Esquema do projeto modelo, MySQL 8.4.
-- Executado automaticamente pelo contêiner na primeira subida
-- (docker-entrypoint-initdb.d), antes do 02-seed.sql.

CREATE TABLE IF NOT EXISTS categoria (
    id    INT          NOT NULL AUTO_INCREMENT,
    nome  VARCHAR(60)  NOT NULL,
    CONSTRAINT pk_categoria PRIMARY KEY (id),
    CONSTRAINT uq_categoria_nome UNIQUE (nome)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE TABLE IF NOT EXISTS produto (
    id            INT            NOT NULL AUTO_INCREMENT,
    sku           VARCHAR(20)    NOT NULL,
    nome          VARCHAR(120)   NOT NULL,
    -- dinheiro e DECIMAL, nunca FLOAT: 0.1 + 0.2 precisa dar 0.30
    preco         DECIMAL(10, 2) NOT NULL,
    quantidade    INT            NOT NULL DEFAULT 0,
    categoria_id  INT            NOT NULL,
    criado_em     TIMESTAMP      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_produto PRIMARY KEY (id),
    CONSTRAINT uq_produto_sku UNIQUE (sku),
    CONSTRAINT ck_produto_preco CHECK (preco >= 0),
    CONSTRAINT ck_produto_quantidade CHECK (quantidade >= 0),
    CONSTRAINT fk_produto_categoria FOREIGN KEY (categoria_id)
        REFERENCES categoria (id)
        ON DELETE RESTRICT
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4;

CREATE INDEX ix_produto_nome ON produto (nome);
