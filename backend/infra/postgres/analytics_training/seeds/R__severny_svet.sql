-- Canonical lesson dataset. Do not mix in the retail_sales training records.
INSERT INTO public.order_items (
    line_item_id, order_id, order_date, customer_id, product, category,
    quantity, unit_price, status
) VALUES
    (2001, 5001, '2026-09-01', 'C101', 'Mug', 'Home', 2, 450, 'completed'),
    (2002, 5001, '2026-09-01', 'C101', 'Notebook', 'Stationery', 3, 180, 'completed'),
    (2003, 5002, '2026-09-02', 'C102', 'Lamp', 'Home', 1, 2400, 'completed'),
    (2004, 5003, '2026-09-02', 'C103', 'Bottle', 'Accessories', 2, 900, 'completed'),
    (2005, 5004, '2026-09-03', 'C104', 'Notebook', 'Stationery', 5, 180, 'completed'),
    (2006, 5005, '2026-09-04', 'C105', 'Bottle', 'Accessories', 1, 900, 'cancelled'),
    (2007, 5006, '2026-09-04', 'C101', 'Mug', 'Home', 1, 450, 'completed'),
    (2008, 5007, '2026-09-05', 'C106', 'Lamp', 'Home', 1, 2400, 'completed'),
    (2009, 5007, '2026-09-05', 'C106', 'Bottle', 'Accessories', 1, 900, 'completed'),
    (2010, 5008, '2026-09-06', 'C107', 'Notebook', 'Stationery', 2, 180, 'completed')
ON CONFLICT (line_item_id) DO NOTHING;
