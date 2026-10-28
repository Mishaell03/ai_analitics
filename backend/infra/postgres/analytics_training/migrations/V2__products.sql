-- PRODUCTS
-- Название товара — стабильный уникальный ключ только для учебного кейса.
-- В коммерческой системе предпочтителен отдельный product_id.
CREATE TABLE IF NOT EXISTS products (
    product TEXT PRIMARY KEY,
    brand TEXT,
    supplier TEXT
);
