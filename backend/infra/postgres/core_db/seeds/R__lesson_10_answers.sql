-- Course 1, module 3, lesson 10. Correct choices: 2, 3, 2, 4, 1, 3.
-- Reuse the image registered by R__lesson_05_answers.sql.
INSERT INTO lesson_media (lesson_id, media_id)
SELECT 10, media_id FROM media_files
WHERE media_key = 'm_72e62512f7eb46e3' AND course_id = 1
ON CONFLICT (lesson_id, media_id) DO NOTHING;

INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (10, 'lesson_10_test_01', '{"type":"choice","correct":["`1`, потому что отсутствует только одно значение."]}'),
    (10, 'lesson_10_test_02', '{"type":"choice","correct":["Повтор `line_item_id` нарушает правило уникальности, а повтор `order_id` может быть нормальным."]}'),
    (10, 'lesson_10_test_03', '{"type":"choice","correct":["Количество товара должно быть строго положительным."]}'),
    (10, 'lesson_10_test_04', '{"type":"choice","correct":["Среднее 5; медиана 2,5."]}'),
    (10, 'lesson_10_test_05', '{"type":"choice","correct":["Оно повышает среднее, но само по себе не доказывает ошибку в данных."]}'),
    (10, 'lesson_10_test_06', '{"type":"choice","correct":["Зафиксировать проблемы, выяснить их причины и определить пригодные для расчёта данные."]}')
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();

-- Pre-recorded reference results; duration=0 is not a sandbox timing measurement.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer)
SELECT 10, seed.exercise_id,
    json_build_object(
        'type', 'code', 'language', 'python', 'value', seed.code,
        'execution', json_build_object(
            'stdout', seed.stdout, 'stderr', '', 'exit_code', 0,
            'timed_out', false, 'duration', 0,
            'output_limited', false, 'memory_limited', false
        )
    )::text
FROM (VALUES
    ('lesson_10_python_01', $python$import pandas as pd
from io import StringIO

csv_text = """line_item_id,order_id,quantity,unit_price,status
6101,8101,2,450,completed
6102,8101,1,180,completed
6103,8102,,900,completed
6104,8103,3,400,completed
6104,8104,1,600,completed
6106,8105,2,700,cancelled
"""

df = pd.read_csv(StringIO(csv_text))

print("Размер:", df.shape)
print("Пропуски:")
print(df.isna().sum())
print("Строки с пропущенным количеством:")
print(df[df["quantity"].isna()][["line_item_id", "order_id"]])

duplicate_mask = df["line_item_id"].duplicated(keep=False)
print("Повторяющиеся line_item_id:")
print(df[duplicate_mask][["line_item_id", "order_id"]])
print("Частота order_id:")
print(df["order_id"].value_counts())
$python$, E'Размер: (6, 5)\nПропуски:\nline_item_id    0\norder_id        0\nquantity        1\nunit_price      0\nstatus          0\ndtype: int64\nСтроки с пропущенным количеством:\n   line_item_id  order_id\n2          6103      8102\nПовторяющиеся line_item_id:\n   line_item_id  order_id\n3          6104      8103\n4          6104      8104\nЧастота order_id:\norder_id\n8101    2\n8102    1\n8103    1\n8104    1\n8105    1\nName: count, dtype: int64\n'),
    ('lesson_10_python_02', $python$import pandas as pd
from io import StringIO

csv_text = """line_item_id,quantity
6201,1
6202,2
6203,3
6204,4
6205,15
"""

df = pd.read_csv(StringIO(csv_text))

print("Среднее:", df["quantity"].mean())
print("Медиана:", df["quantity"].median())
print("Минимум:", df["quantity"].min())
print("Максимум:", df["quantity"].max())
$python$, E'Среднее: 5.0\nМедиана: 3.0\nМинимум: 1\nМаксимум: 15\n'),
    ('lesson_10_python_03', $python$import pandas as pd
from io import StringIO

csv_text = """line_item_id,order_id,order_date,customer_id,product,category,quantity,unit_price,status
7301,9301,2026-09-15,C301,Mug,Home,2,450,completed
7302,9301,2026-09-15,C301,Notebook,Stationery,3,180,completed
7303,9302,2026-09-16,C302,Lamp,Home,1,2400,completed
7304,9303,2026-09-16,C303,Bottle,Accessories,0,900,completed
7305,9304,2026-09-17,C304,Notebook,Stationery,,180,completed
7306,9305,2026-09-17,C305,Mug,Home,2,-450,completed
7307,9306,2026-09-18,C306,Bottle,Accessories,1,900,processing
7308,9307,2026-09-18,C307,Lamp,Home,4,2400,completed
7308,9307,2026-09-18,C307,Notebook,Stationery,2,180,completed
"""

df = pd.read_csv(StringIO(csv_text))

print("Размер:", df.shape)
print("Пропуски:")
print(df.isna().sum())

duplicate_mask = df["line_item_id"].duplicated(keep=False)
print("Повторяющиеся line_item_id:")
print(df[duplicate_mask][["line_item_id", "order_id"]])
print("Недопустимые количества:")
print(df[df["quantity"] <= 0][["line_item_id", "quantity"]])
print("Отрицательные цены:")
print(df[df["unit_price"] < 0][["line_item_id", "unit_price"]])

unknown_status_mask = (
    (df["status"] != "completed")
    & (df["status"] != "cancelled")
)
print("Неизвестные статусы:")
print(df[unknown_status_mask][["line_item_id", "status"]])

# Отдельная подвыборка для предварительной статистики.
# Исходный DataFrame не изменяем.
valid_df = df[
    (df["status"] == "completed")
    & (df["line_item_id"].isna() == False)
    & (duplicate_mask == False)
    & (df["quantity"].isna() == False)
    & (df["quantity"] > 0)
    & (df["unit_price"] >= 0)
].copy()

print("Проверенная подвыборка:")
print(valid_df[["line_item_id", "quantity"]])
print("Записей в подвыборке:", len(valid_df))
print("Среднее:", valid_df["quantity"].mean())
print("Медиана:", valid_df["quantity"].median())
print("Минимум:", valid_df["quantity"].min())
print("Максимум:", valid_df["quantity"].max())
$python$, E'Размер: (9, 9)\nПропуски:\nline_item_id    0\norder_id        0\norder_date      0\ncustomer_id     0\nproduct         0\ncategory        0\nquantity        1\nunit_price      0\nstatus          0\ndtype: int64\nПовторяющиеся line_item_id:\n   line_item_id  order_id\n7          7308      9307\n8          7308      9307\nНедопустимые количества:\n   line_item_id  quantity\n3          7304       0.0\nОтрицательные цены:\n   line_item_id  unit_price\n5          7306        -450\nНеизвестные статусы:\n   line_item_id      status\n6          7307  processing\nПроверенная подвыборка:\n   line_item_id  quantity\n0          7301       2.0\n1          7302       3.0\n2          7303       1.0\nЗаписей в подвыборке: 3\nСреднее: 2.0\nМедиана: 2.0\nМинимум: 1.0\nМаксимум: 3.0\n')
) AS seed(exercise_id, code, stdout)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();
