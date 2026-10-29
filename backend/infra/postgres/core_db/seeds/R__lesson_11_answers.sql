-- Course 1 / module 4 / lesson 11. Correct options: 2, 3, 4, 1, 2, 3.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (11, 'lesson_11_test_01', $answer${"type":"choice","correct":["`SELECT product, quantity FROM order_items;`"]}$answer$),
    (11, 'lesson_11_test_02', $answer${"type":"choice","correct":["`WHERE status = 'completed'`"]}$answer$),
    (11, 'lesson_11_test_03', $answer${"type":"choice","correct":["2004 и 2007."]}$answer$),
    (11, 'lesson_11_test_04', $answer${"type":"choice","correct":["Позиции 2003, 2008, 2004 — именно в таком порядке."]}$answer$),
    (11, 'lesson_11_test_05', $answer${"type":"choice","correct":["3 строки и 2 разных заказа."]}$answer$),
    (11, 'lesson_11_test_06', $answer${"type":"choice","correct":["2700 рублей."]}$answer$)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer, updated_at = NOW();

-- PostgreSQL runner serializes numeric/Decimal values as strings.
-- ordered=false means row order is not a criterion; duplicates still count.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer)
SELECT 11, seed.exercise_id,
    json_build_object(
        'type', 'code', 'language', 'sql', 'value', seed.code, 'ordered', seed.ordered,
        'execution', json_build_object(
            'stdout', seed.result::text, 'stderr', '', 'exit_code', 0,
            'timed_out', false, 'duration', 0,
            'output_limited', false, 'memory_limited', false
        )
    )::text
FROM (VALUES
    ('lesson_11_sql_01', $sql$SELECT line_item_id, product, quantity, status
FROM order_items
WHERE status = 'completed';$sql$, false,
    $result${"columns":["line_item_id","product","quantity","status"],"rows":[[2001,"Mug",2,"completed"],[2002,"Notebook",3,"completed"],[2003,"Lamp",1,"completed"],[2004,"Bottle",2,"completed"],[2005,"Notebook",5,"completed"],[2007,"Mug",1,"completed"],[2008,"Lamp",1,"completed"],[2009,"Bottle",1,"completed"],[2010,"Notebook",2,"completed"]]}$result$),
    ('lesson_11_sql_02', $sql$SELECT line_item_id, product, unit_price
FROM order_items
WHERE status = 'completed'
  AND unit_price >= 900
ORDER BY unit_price DESC, line_item_id ASC
LIMIT 3;$sql$, true,
    $result${"columns":["line_item_id","product","unit_price"],"rows":[[2003,"Lamp","2400.00"],[2008,"Lamp","2400.00"],[2004,"Bottle","900.00"]]}$result$),
    ('lesson_11_sql_03_total', $sql$SELECT COUNT(*) FROM order_items;$sql$, true,
    $result${"columns":["count"],"rows":[[10]]}$result$),
    ('lesson_11_sql_03_completed', $sql$SELECT COUNT(*) FROM order_items WHERE status = 'completed';$sql$, true,
    $result${"columns":["count"],"rows":[[9]]}$result$),
    ('lesson_11_sql_03_orders', $sql$SELECT COUNT(DISTINCT order_id) FROM order_items WHERE status = 'completed';$sql$, true,
    $result${"columns":["count"],"rows":[[7]]}$result$),
    ('lesson_11_sql_03_quantity', $sql$SELECT SUM(quantity) FROM order_items WHERE status = 'completed';$sql$, true,
    $result${"columns":["sum"],"rows":[[18]]}$result$),
    ('lesson_11_sql_03_revenue', $sql$SELECT SUM(quantity * unit_price) FROM order_items WHERE status = 'completed';$sql$, true,
    $result${"columns":["sum"],"rows":[["10650.00"]]}$result$)
) AS seed(exercise_id, code, ordered, result)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer, updated_at = NOW();

-- Media m_72e62512f7eb67e3 is referenced in the Markdown but its file has
-- not yet been supplied. Register metadata only after inspecting the real file.
