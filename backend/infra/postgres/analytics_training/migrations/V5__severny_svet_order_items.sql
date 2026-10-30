-- Preserve the original retail dataset under a distinct, explicit name.
-- Lessons 11 onward use the canonical ten-row Severny Svet dataset instead.
ALTER TABLE public.order_items RENAME TO retail_order_items;

CREATE TABLE public.order_items (
    line_item_id INTEGER PRIMARY KEY,
    order_id INTEGER NOT NULL,
    order_date DATE NOT NULL,
    customer_id TEXT NOT NULL,
    product TEXT NOT NULL,
    category TEXT NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    status TEXT NOT NULL CHECK (status IN ('completed', 'cancelled'))
);
