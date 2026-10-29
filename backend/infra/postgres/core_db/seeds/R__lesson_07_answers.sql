-- Lesson content: infra/minio/seeds/course-content/1/3/7.md.
-- Database lesson_id and logical course sequence are both 7.
-- Correct option numbers: 3, 1, 4, 2, 3, 2.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (7, 'lesson_07_test_01', '{"type":"choice","correct":["`(2, 2)`"]}'),
    (7, 'lesson_07_test_02', '{"type":"choice","correct":["Первые две строки, не изменяя количество строк исходного DataFrame."]}'),
    (7, 'lesson_07_test_03', '{"type":"choice","correct":["`df.columns`"]}'),
    (7, 'lesson_07_test_04', '{"type":"choice","correct":["Тип нужно проверить: без специального указания дата может остаться текстовым столбцом."]}'),
    (7, 'lesson_07_test_05', '{"type":"choice","correct":["Один пропуск."]}'),
    (7, 'lesson_07_test_06', '{"type":"choice","correct":["`2`, потому что разных номеров заказа два."]}')
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();

-- Diagram embedded in lesson 7.
INSERT INTO media_files (
    media_key, course_id, object_key, kind, content_type, size_bytes,
    width, height, original_name
) VALUES (
    'm_c152ed1ad3274162', 1, '1/media/m_c152ed1ad3274162.png',
    'image', 'image/png', 262396, 1672, 941, 'm_c152ed1ad3274162.png'
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
SELECT 7, media_id
FROM media_files
WHERE media_key = 'm_c152ed1ad3274162' AND course_id = 1
ON CONFLICT (lesson_id, media_id) DO NOTHING;

-- Reference executions are pre-recorded; automatic grading compares stdout.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer)
SELECT 7, seed.exercise_id,
    json_build_object(
        'type', 'code', 'language', 'python', 'value', seed.code,
        'execution', json_build_object(
            'stdout', seed.stdout, 'stderr', '', 'exit_code', 0,
            'timed_out', false, 'duration', 0,
            'output_limited', false, 'memory_limited', false
        )
    )::text
FROM (VALUES
    ('lesson_07_python_01', $python$import pandas as pd
from io import StringIO

csv_text = """product,category,quantity,unit_price
Mug,Home,2,450
Notebook,Stationery,3,180
Bottle,Accessories,1,900
Lamp,Home,1,2400
"""

df = pd.read_csv(StringIO(csv_text))

print("Первые три строки:")
print(df.head(3).to_string(index=False))
print("Размер:", df.shape)
print("Названия столбцов:", list(df.columns))
print("Товарных позиций:", df.shape[0])
print("Характеристик:", df.shape[1])
$python$, E'Первые три строки:\n product    category  quantity  unit_price\n    Mug         Home         2         450\nNotebook  Stationery         3         180\n  Bottle Accessories         1         900\nРазмер: (4, 4)\nНазвания столбцов: [\'product\', \'category\', \'quantity\', \'unit_price\']\nТоварных позиций: 4\nХарактеристик: 4\n'),
    ('lesson_07_python_02', $python$import pandas as pd
from io import StringIO

csv_text = """line_item_id,product,quantity,unit_price,status
9101,Mug,2,450,completed
9102,Notebook,,180,completed
9103,Lamp,two,2400,completed
9104,Bottle,1,-900,cancelled
9105,Mug,3,450,processing
"""

df = pd.read_csv(StringIO(csv_text))
status_counts = df["status"].value_counts()

print("Размер:", df.shape)
print("Тип quantity:", df["quantity"].dtype)
print("Пропусков quantity:", int(df["quantity"].isna().sum()))
print("Статусы:", ", ".join(
    f"{status}={int(status_counts.get(status, 0))}"
    for status in ["completed", "cancelled", "processing"]
))
print("Позиция 9104: unit_price =", int(df.loc[df["line_item_id"] == 9104, "unit_price"].iloc[0]))
$python$, E'Размер: (5, 5)\nТип quantity: object\nПропусков quantity: 1\nСтатусы: completed=3, cancelled=1, processing=1\nПозиция 9104: unit_price = -900\n'),
    ('lesson_07_python_03', $python$import pandas as pd
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
status_counts = df["status"].value_counts()

print("Первые пять строк:")
print(df.head().to_string(index=False))
print("Размер:", df.shape)
print("Столбцы:", ", ".join(df.columns))
print("Тип order_date:", df["order_date"].dtype)
print("Всего пропусков:", int(df.isna().sum().sum()))
print("Статусы:", ", ".join(
    f"{status}={int(status_counts.get(status, 0))}"
    for status in ["completed", "cancelled"]
))
print("Разных заказов всего:", df["order_id"].nunique())
$python$, E'Первые пять строк:\n line_item_id  order_id order_date customer_id  product    category  quantity  unit_price    status\n         2001      5001 2026-09-01        C101      Mug        Home         2         450 completed\n         2002      5001 2026-09-01        C101 Notebook  Stationery         3         180 completed\n         2003      5002 2026-09-02        C102     Lamp        Home         1        2400 completed\n         2004      5003 2026-09-02        C103   Bottle Accessories         2         900 completed\n         2005      5004 2026-09-03        C104 Notebook  Stationery         5         180 completed\nРазмер: (10, 9)\nСтолбцы: line_item_id, order_id, order_date, customer_id, product, category, quantity, unit_price, status\nТип order_date: object\nВсего пропусков: 0\nСтатусы: completed=9, cancelled=1\nРазных заказов всего: 8\n')
) AS seed(exercise_id, code, stdout)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();
