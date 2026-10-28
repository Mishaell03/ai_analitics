-- ORDERS
CREATE TABLE IF NOT EXISTS orders (
    order_id BIGINT PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL REFERENCES customers(customer_id),
    sales_channel TEXT
);

CREATE INDEX IF NOT EXISTS ix_orders_customer_id ON orders(customer_id);
