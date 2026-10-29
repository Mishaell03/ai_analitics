-- Course 1 / module 4 / lesson 13. Correct choices: 2, 3, 1, 4, 2, 3.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (13, 'lesson_13_test_01', $answer${"type":"choice","correct":["Столбчатая диаграмма с категориями и выручкой в рублях."]}$answer$),
    (13, 'lesson_13_test_02', $answer${"type":"choice","correct":["Линия с месяцами в хронологическом порядке и отмеченными точками."]}$answer$),
    (13, 'lesson_13_test_03', $answer${"type":"choice","correct":["`plt.bar(names, revenue); plt.ylabel(\"Выручка, руб.\"); plt.show()`"]}$answer$),
    (13, 'lesson_13_test_04', $answer${"type":"choice","correct":["В феврале выручка ниже января, а в марте выше февраля, но ниже января."]}$answer$),
    (13, 'lesson_13_test_05', $answer${"type":"choice","correct":["Начать числовую ось с нуля и ясно указать, что измеряется в рублях."]}$answer$),
    (13, 'lesson_13_test_06', $answer${"type":"choice","correct":["Наблюдалось снижение, затем увеличение; причины и долгосрочные тенденции ещё неизвестны."]}$answer$)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer, updated_at = NOW();

-- Stable exercise IDs, not auto-increment answer_id, link Markdown to experts.
-- Chart data are checked by lesson-13 rubric; PNG styling is not compared.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer)
SELECT 13, seed.exercise_id,
    json_build_object('type', 'code', 'language', 'python',
                      'check_mode', 'graded', 'value', seed.code)::text
FROM (VALUES
    ('lesson_13_python_01', $python$import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

csv_text = """category,completed_lines,units_sold,revenue
Электроника,5,5,220000
Аксессуары,10,13,37500
Бытовая техника,6,7,34700
Канцелярия,5,24,5540
Товары для дома,6,13,5040
"""

df = pd.read_csv(StringIO(csv_text))
sorted_df = df.sort_values(by="revenue", ascending=False)
print("Общая выручка, руб.:", sorted_df["revenue"].sum())
print("Продано единиц:", sorted_df["units_sold"].sum())
print(sorted_df[["category", "revenue"]].to_string(index=False))

plt.figure(figsize=(9, 5))
plt.barh(sorted_df["category"], sorted_df["revenue"])
plt.gca().invert_yaxis()
plt.xlabel("Учебная выручка, руб.")
plt.ylabel("Категория товаров")
plt.title("Учебная выручка RETAIL SALES по категориям, январь–март 2025")
plt.xlim(left=0)
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.show()
$python$),
    ('lesson_13_python_02', $python$import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

csv_text = """month,revenue
2025-01,129950
2025-02,55310
2025-03,117520
"""

df = pd.read_csv(StringIO(csv_text)).sort_values(by="month")
january = df["revenue"].iloc[0]
february = df["revenue"].iloc[1]
march = df["revenue"].iloc[2]
print("Выручка за три месяца, руб.:", df["revenue"].sum())
print("Февраль минус январь, руб.:", february - january)
print("Март минус февраль, руб.:", march - february)

plt.figure(figsize=(8, 4))
plt.plot(df["month"], df["revenue"], marker="o")
plt.title("Учебная выручка RETAIL SALES по месяцам, январь–март 2025")
plt.xlabel("Месяц")
plt.ylabel("Учебная выручка, руб.")
plt.grid(alpha=0.3)
plt.tight_layout()
plt.show()
$python$),
    ('lesson_13_python_03', $python$import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

csv_text = """line_item_id,order_date,category,quantity,unit_price,status
1,2025-01-05,Электроника,1,65000.00,completed
2,2025-01-05,Аксессуары,1,1500.00,completed
3,2025-01-07,Электроника,1,32000.00,completed
4,2025-01-07,Аксессуары,2,4500.00,completed
5,2025-01-10,Бытовая техника,1,8500.00,completed
6,2025-01-10,Товары для дома,2,450.00,completed
7,2025-01-12,Бытовая техника,1,2800.00,cancelled
8,2025-01-18,Аксессуары,1,3500.00,completed
9,2025-01-18,Канцелярия,3,250.00,completed
10,2025-01-21,Бытовая техника,1,2800.00,completed
11,2025-01-21,Товары для дома,4,450.00,completed
12,2025-01-28,Аксессуары,1,4200.00,completed
13,2025-02-02,Электроника,1,31000.00,completed
14,2025-02-02,Аксессуары,1,1400.00,completed
15,2025-02-05,Бытовая техника,1,8000.00,completed
16,2025-02-05,Товары для дома,2,400.00,completed
17,2025-02-09,Электроника,1,64000.00,cancelled
18,2025-02-09,Аксессуары,1,1400.00,cancelled
19,2025-02-13,Канцелярия,5,250.00,completed
20,2025-02-16,Аксессуары,2,3300.00,completed
21,2025-02-16,Аксессуары,2,1400.00,completed
22,2025-02-20,Бытовая техника,1,2600.00,completed
23,2025-02-20,Товары для дома,1,400.00,completed
24,2025-02-25,Канцелярия,2,230.00,completed
25,2025-03-03,Аксессуары,1,4000.00,completed
26,2025-03-03,Электроника,1,30000.00,completed
27,2025-03-07,Бытовая техника,1,7800.00,completed
28,2025-03-07,Товары для дома,1,0.00,completed
29,2025-03-11,Аксессуары,1,3200.00,cancelled
30,2025-03-15,Канцелярия,10,220.00,completed
31,2025-03-15,Товары для дома,3,380.00,completed
32,2025-03-21,Электроника,1,62000.00,completed
33,2025-03-21,Аксессуары,1,1300.00,completed
34,2025-03-21,Аксессуары,1,3200.00,completed
35,2025-03-28,Бытовая техника,2,2500.00,completed
36,2025-03-28,Канцелярия,4,220.00,completed
"""

df = pd.read_csv(StringIO(csv_text))
completed_df = df[df["status"] == "completed"].copy()
completed_df["line_revenue"] = completed_df["quantity"] * completed_df["unit_price"]
category_revenue = completed_df.groupby("category")["line_revenue"].sum().sort_values(ascending=False)
total_revenue = completed_df["line_revenue"].sum()
grouped_total = category_revenue.sum()
print("Завершённых позиций:", len(completed_df))
print("Выручка по позициям, руб.:", total_revenue)
print("Выручка по категориям, руб.:", grouped_total)
print("Итоги совпадают:", total_revenue == grouped_total)
print(category_revenue)

plt.figure(figsize=(9, 5))
plt.barh(category_revenue.index, category_revenue.values)
plt.gca().invert_yaxis()
plt.title("Учебная выручка RETAIL SALES по категориям, январь–март 2025")
plt.xlabel("Учебная выручка, руб.")
plt.ylabel("Категория")
plt.xlim(left=0)
plt.grid(axis="x", alpha=0.3)
plt.tight_layout()
plt.show()
$python$)
) AS seed(exercise_id, code)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer, updated_at = NOW();
