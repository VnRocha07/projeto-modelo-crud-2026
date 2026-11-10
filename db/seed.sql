-- Carga inicial. SQL portavel: roda igual no MySQL e no SQLite.
-- Tambem e o que o endpoint POST /api/_test/reset executa antes de cada teste E2E,
-- por isso comeca apagando: os testes precisam partir sempre do mesmo estado.

DELETE FROM produto;
DELETE FROM categoria;

INSERT INTO categoria (id, nome) VALUES
    (1, 'Eletrônicos'),
    (2, 'Papelaria'),
    (3, 'Alimentos');

INSERT INTO produto (id, sku, nome, preco, quantidade, categoria_id) VALUES
    (1, 'ELE-001', 'Mouse sem fio',       79.90, 12, 1),
    (2, 'ELE-002', 'Teclado mecânico',   349.00,  3, 1),
    (3, 'PAP-001', 'Caderno 10 matérias', 32.50, 40, 2),
    (4, 'PAP-002', 'Caneta azul',          2.10,  0, 2),
    (5, 'ALI-001', 'Café 500 g',          24.90,  8, 3);
