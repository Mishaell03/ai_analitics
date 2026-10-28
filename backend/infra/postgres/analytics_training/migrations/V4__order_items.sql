-- ORDER ITEMS
CREATE TABLE IF NOT EXISTS order_items (
    line_item_id BIGINT PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(order_id),
    order_date DATE NOT NULL,
    customer_id VARCHAR(20) NOT NULL REFERENCES customers(customer_id),
    product TEXT NOT NULL REFERENCES products(product),
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price NUMERIC(12,2) NOT NULL,
    status VARCHAR(20) NOT NULL,

    CONSTRAINT ck_order_items_quantity_positive CHECK (quantity > 0),
    CONSTRAINT ck_order_items_unit_price_nonnegative CHECK (unit_price >= 0),
    CONSTRAINT ck_order_items_status CHECK (status IN ('completed', 'cancelled'))
);

CREATE INDEX IF NOT EXISTS ix_order_items_order_id ON order_items(order_id);
CREATE INDEX IF NOT EXISTS ix_order_items_customer_id ON order_items(customer_id);
CREATE INDEX IF NOT EXISTS ix_order_items_product ON order_items(product);
CREATE INDEX IF NOT EXISTS ix_order_items_order_date ON order_items(order_date);
