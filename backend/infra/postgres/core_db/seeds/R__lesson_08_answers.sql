-- Answers and references for course 1, module 3, lesson 8.
-- Correct option numbers: 3, 2, 4, 1, 3, 2.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (8, 'lesson_08_test_01', '{"type":"choice","correct":["`True`, `False`, `True`."]}'),
    (8, 'lesson_08_test_02', '{"type":"choice","correct":["`3`"]}'),
    (8, 'lesson_08_test_03', '{"type":"choice","correct":["`df[(df[\"status\"] == \"completed\") & (df[\"quantity\"] >= 2)]`"]}'),
    (8, 'lesson_08_test_04', '{"type":"choice","correct":["`df[[\"product\", \"quantity\"]]`"]}'),
    (8, 'lesson_08_test_05', '{"type":"choice","correct":["`df.sort_values(by=\"unit_price\", ascending=False)`"]}'),
    (8, 'lesson_08_test_06', '{"type":"choice","correct":["3 строки и 2 уникальных заказа."]}')
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();

INSERT INTO exercise_answers (lesson_id, exercise_id, answer)
SELECT 8, seed.exercise_id,
    json_build_object(
        'type', 'code', 'language', 'python', 'value', seed.code,
        'execution', json_build_object(
            'stdout', seed.stdout, 'stderr', '', 'exit_code', 0,
            'timed_out', false, 'duration', 0,
            'output_limited', false, 'memory_limited', false
        )
    )::text
FROM (VALUES
    ('lesson_08_python_01', $python$import pandas as pd
from io import StringIO

csv_text = """line_item_id,product,quantity,status
8101,Mug,2,completed
8102,Bottle,1,cancelled
8103,Lamp,1,completed
8104,Notebook,4,completed
8105,Mug,3,cancelled
"""

df = pd.read_csv(StringIO(csv_text))
completed_df = df[df["status"] == "completed"]

print(completed_df.to_csv(index=False).rstrip())
print("Завершённых позиций:", len(completed_df))
print("Исключено строк:", len(df) - len(completed_df))
$python$, E'line_item_id,product,quantity,status\n8101,Mug,2,completed\n8103,Lamp,1,completed\n8104,Notebook,4,completed\nЗавершённых позиций: 3\nИсключено строк: 2\n'),
    ('lesson_08_python_02', $python$import pandas as pd
from io import StringIO

csv_text = """line_item_id,product,category,quantity,unit_price,status
8201,Mug,Home,3,450,completed
8202,Lamp,Home,1,2400,completed
8203,Bottle,Accessories,2,900,cancelled
8204,Notebook,Stationery,5,180,completed
8205,Bottle,Accessories,2,950,completed
8206,Mug,Home,2,400,completed
"""

df = pd.read_csv(StringIO(csv_text))
filtered_df = df[
    (df["status"] == "completed")
    & (df["quantity"] >= 2)
]
columns_df = filtered_df[["line_item_id", "product", "quantity", "unit_price"]]
sorted_df = columns_df.sort_values(by="unit_price", ascending=False)

print(sorted_df.to_csv(index=False).rstrip())
print("Подходящих позиций:", len(sorted_df))
$python$, E'line_item_id,product,quantity,unit_price\n8205,Bottle,2,950\n8201,Mug,3,450\n8206,Mug,2,400\n8204,Notebook,5,180\nПодходящих позиций: 4\n'),
    ('lesson_08_python_03', $python$import pandas as pd
from io import StringIO

csv_text = """line_item_id,order_id,order_date,customer_id,product,category,quantity,unit_price,status
2001,5001,2026-09-01,C101,Mug,Home,2,450,completed
2002,5001,2026-09-01,C101,Notebook,Stationery,3,180,completed
2003,5002,2026-09-02,C102,Lamp,Home,1,2400,completed
2004,5003,2026-09-02,C103,Bottle,Accessories,2,900,completed
2005,5004,2026-09-03,C104,Notebook,Stationery,5,180,completed
2006,5005,2026-09-04,C105,Bottle,Accessories,1,900,cancelled
2007,5006,2026-09-04,C101,Mug,Home,1,450,completed
2008,5007,2026-09-05,C106,Lamp,Home,1,2400,completed
2009,5007,2026-09-05,C106,Bottle,Accessories,1,900,completed
2010,5008,2026-09-06,C107,Notebook,Stationery,2,180,completed
"""

df = pd.read_csv(StringIO(csv_text))
completed_df = df[df["status"] == "completed"]
expensive_df = completed_df[completed_df["unit_price"] >= 900]
sorted_df = expensive_df.sort_values(by="unit_price", ascending=False, kind="stable")

print("Завершённых позиций:", len(completed_df))
print("Уникальных завершённых заказов:", completed_df["order_id"].nunique())
print("Дорогих завершённых позиций:", len(sorted_df))
print(sorted_df[["line_item_id", "product", "unit_price"]].to_csv(index=False).rstrip())
$python$, E'Завершённых позиций: 9\nУникальных завершённых заказов: 7\nДорогих завершённых позиций: 4\nline_item_id,product,unit_price\n2003,Lamp,2400\n2008,Lamp,2400\n2004,Bottle,900\n2009,Bottle,900\n')
) AS seed(exercise_id, code, stdout)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();

-- Diagram used in lesson 8.
INSERT INTO media_files (
    media_key, course_id, object_key, kind, content_type, size_bytes,
    width, height, original_name
) VALUES (
    'm_cc29e914deee46db', 1, '1/media/m_cc29e914deee46db.png',
    'image', 'image/png', 234407, 1672, 941, 'm_cc29e914deee46db.png'
)
ON CONFLICT (media_key) DO UPDATE SET
    object_key = EXCLUDED.object_key,
    kind = EXCLUDED.kind,
    content_type = EXCLUDED.content_type,
    size_bytes = EXCLUDED.size_bytes,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    original_name = EXCLUDED.original_name,
    updated_at = NOW()
WHERE media_files.course_id = EXCLUDED.course_id;

INSERT INTO lesson_media (lesson_id, media_id)
SELECT 8, media_id
FROM media_files
WHERE media_key = 'm_cc29e914deee46db' AND course_id = 1
ON CONFLICT (lesson_id, media_id) DO NOTHING;
