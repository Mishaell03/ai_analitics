-- Course 1, module 5, lesson 14. Correct choices: 3, 1, 4, 2, 3, 2.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (14, 'lesson_14_test_01', $answer${"type":"choice","correct":["Проверить пропущенное количество; бесплатную позицию не исключать только из-за нулевой цены."]}$answer$),
    (14, 'lesson_14_test_02', $answer${"type":"choice","correct":["2 позиции, 1 заказ, 5 единиц."]}$answer$),
    (14, 'lesson_14_test_03', $answer${"type":"choice","correct":["800 рублей — учитывается только завершённая позиция."]}$answer$),
    (14, 'lesson_14_test_04', $answer${"type":"choice","correct":["Суммарную выручку каждой категории по выбранным строкам."]}$answer$),
    (14, 'lesson_14_test_05', $answer${"type":"choice","correct":["Столбчатая диаграмма для категорий и линейный график для месяцев."]}$answer$),
    (14, 'lesson_14_test_06', $answer${"type":"choice","correct":["Можно описать изменения, но их причины и сезонность без дополнительных данных не установлены."]}$answer$)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer, updated_at = NOW();

-- CSV is shared only while generating seed rows. Every stored expert program
-- includes its own imports and all 36 rows and can run independently.
WITH dataset(csv) AS (VALUES ($csv$line_item_id,order_id,order_date,customer_id,product,category,quantity,unit_price,status
1,1001,2025-01-05,C001,Ноутбук Альфа 14,Электроника,1,65000.00,completed
2,1001,2025-01-05,C001,Мышь беспроводная,Аксессуары,1,1500.00,completed
3,1002,2025-01-07,C002,Смартфон Бета 128,Электроника,1,32000.00,completed
4,1002,2025-01-07,C002,Наушники Гамма,Аксессуары,2,4500.00,completed
5,1003,2025-01-10,C003,Кофеварка домашняя,Бытовая техника,1,8500.00,completed
6,1003,2025-01-10,C003,Кружка керамическая,Товары для дома,2,450.00,completed
7,1004,2025-01-12,C004,Чайник электрический,Бытовая техника,1,2800.00,cancelled
8,1005,2025-01-18,C001,Клавиатура компактная,Аксессуары,1,3500.00,completed
9,1005,2025-01-18,C001,Блокнот А5,Канцелярия,3,250.00,completed
10,1006,2025-01-21,C005,Чайник электрический,Бытовая техника,1,2800.00,completed
11,1006,2025-01-21,C005,Кружка керамическая,Товары для дома,4,450.00,completed
12,1007,2025-01-28,C006,Наушники Гамма,Аксессуары,1,4200.00,completed
13,1008,2025-02-02,C007,Смартфон Бета 128,Электроника,1,31000.00,completed
14,1008,2025-02-02,C007,Мышь беспроводная,Аксессуары,1,1400.00,completed
15,1009,2025-02-05,C002,Кофеварка домашняя,Бытовая техника,1,8000.00,completed
16,1009,2025-02-05,C002,Кружка керамическая,Товары для дома,2,400.00,completed
17,1010,2025-02-09,C008,Ноутбук Альфа 14,Электроника,1,64000.00,cancelled
18,1010,2025-02-09,C008,Мышь беспроводная,Аксессуары,1,1400.00,cancelled
19,1011,2025-02-13,C003,Блокнот А5,Канцелярия,5,250.00,completed
20,1012,2025-02-16,C009,Клавиатура компактная,Аксессуары,2,3300.00,completed
21,1012,2025-02-16,C009,Мышь беспроводная,Аксессуары,2,1400.00,completed
22,1013,2025-02-20,C004,Чайник электрический,Бытовая техника,1,2600.00,completed
23,1013,2025-02-20,C004,Кружка керамическая,Товары для дома,1,400.00,completed
24,1014,2025-02-25,C010,Блокнот А5,Канцелярия,2,230.00,completed
25,1015,2025-03-03,C001,Наушники Гамма,Аксессуары,1,4000.00,completed
26,1015,2025-03-03,C001,Смартфон Бета 128,Электроника,1,30000.00,completed
27,1016,2025-03-07,C005,Кофеварка домашняя,Бытовая техника,1,7800.00,completed
28,1016,2025-03-07,C005,Кружка керамическая,Товары для дома,1,0.00,completed
29,1017,2025-03-11,C006,Клавиатура компактная,Аксессуары,1,3200.00,cancelled
30,1018,2025-03-15,C007,Блокнот А5,Канцелярия,10,220.00,completed
31,1018,2025-03-15,C007,Кружка керамическая,Товары для дома,3,380.00,completed
32,1019,2025-03-21,C008,Ноутбук Альфа 14,Электроника,1,62000.00,completed
33,1019,2025-03-21,C008,Мышь беспроводная,Аксессуары,1,1300.00,completed
34,1019,2025-03-21,C008,Клавиатура компактная,Аксессуары,1,3200.00,completed
35,1020,2025-03-28,C009,Чайник электрический,Бытовая техника,2,2500.00,completed
36,1020,2025-03-28,C009,Блокнот А5,Канцелярия,4,220.00,completed$csv$)),
solutions(exercise_id, body) AS (VALUES
    ('lesson_14_python_01', $python$df = pd.read_csv(StringIO(csv_text))
print("Размер таблицы (строки, столбцы):", df.shape)
print("Пропуски по столбцам:")
print(df.isna().sum())
repeated_ids = df["line_item_id"].duplicated(keep=False)
print("Повторяющиеся уникальные line_item_id:", repeated_ids.sum())
print("Разных заказов среди всех статусов:", df["order_id"].nunique())
print("Статусы:")
print(df["status"].value_counts())
cancelled_df = df[df["status"] == "cancelled"]
print("Отменённых позиций:", len(cancelled_df))
print("Отменённые ID:", cancelled_df["line_item_id"].tolist())
print("Количество <= 0:", len(df[df["quantity"] <= 0]))
print("Отрицательных цен:", len(df[df["unit_price"] < 0]))
unknown_status = df[(df["status"] != "completed") & (df["status"] != "cancelled")]
print("Неожиданных статусов:", len(unknown_status))
free_completed = df[(df["status"] == "completed") & (df["unit_price"] == 0)]
print("Завершённые бесплатные позиции:")
print(free_completed[["line_item_id", "quantity", "unit_price"]])
completed_df = df[df["status"] == "completed"].copy()
completed_df["line_revenue"] = completed_df["quantity"] * completed_df["unit_price"]
print("Завершённых товарных позиций:", len(completed_df))
print("Уникальных завершённых заказов:", completed_df["order_id"].nunique())
print("Продано единиц:", completed_df["quantity"].sum())
print("Учебная выручка, руб.:", completed_df["line_revenue"].sum())
print("Вывод: в учебной модели обязательные поля заполнены, уникальные ID не повторяются;")
print("завершённые и отменённые позиции разделены. Бесплатная завершённая позиция допустима.")
print("Ограничение: в наборе нет себестоимости и других затрат — прибыль не определена.")
$python$),
    ('lesson_14_python_02', $python$df = pd.read_csv(StringIO(csv_text))
completed_df = df[df["status"] == "completed"].copy()
completed_df["line_revenue"] = completed_df["quantity"] * completed_df["unit_price"]
category_summary = completed_df.groupby("category")[["quantity", "line_revenue"]].sum().sort_values(by="line_revenue", ascending=False)
print("Проданные единицы и выручка по категориям:")
print(category_summary)
revenue_total = completed_df["line_revenue"].sum()
category_total = category_summary["line_revenue"].sum()
print("Общая завершённая выручка, руб.:", revenue_total)
print("Итог категорий, руб.:", category_total)
print("Итоги совпадают:", revenue_total == category_total)
leader = category_summary.index[0]
units_leader = category_summary["quantity"].idxmax()
print("Лидер по выручке:", leader)
print("Лидер по количеству единиц:", units_leader)
print("Вывод: лидер по выручке не обязан лидировать по количеству единиц.")
print("Ограничение: выручка без себестоимости не равна прибыли.")
plot_data = category_summary.sort_values(by="line_revenue", ascending=True)
plt.figure(figsize=(10, 5))
plt.barh(plot_data.index, plot_data["line_revenue"])
plt.title("Учебная выручка по категориям, январь–март 2025")
plt.xlabel("Выручка, руб.")
plt.ylabel("Категория")
plt.xlim(left=0)
plt.grid(axis="x", alpha=0.25)
plt.tight_layout()
plt.show()
$python$),
    ('lesson_14_python_03', $python$df = pd.read_csv(StringIO(csv_text))
completed_df = df[df["status"] == "completed"].copy()
completed_df["line_revenue"] = completed_df["quantity"] * completed_df["unit_price"]
completed_df["month"] = completed_df["order_date"].str[:7]
monthly_revenue = completed_df.groupby("month")["line_revenue"].sum().sort_index()
print("Учебная выручка по месяцам:")
print(monthly_revenue)
jan_to_feb = monthly_revenue["2025-02"] - monthly_revenue["2025-01"]
feb_to_mar = monthly_revenue["2025-03"] - monthly_revenue["2025-02"]
print("Изменение февраль минус январь, руб.:", jan_to_feb)
print("Изменение март минус февраль, руб.:", feb_to_mar)
all_completed_revenue = completed_df["line_revenue"].sum()
print("Общий итог, руб.:", all_completed_revenue)
print("Сумма месяцев, руб.:", monthly_revenue.sum())
print("Суммы совпадают:", monthly_revenue.sum() == all_completed_revenue)
category_revenue = completed_df.groupby("category")["line_revenue"].sum().sort_values(ascending=False)
print("Ведущая категория:", category_revenue.index[0])
plt.figure(figsize=(9, 5))
plt.plot(monthly_revenue.index, monthly_revenue.values, marker="o")
plt.title("Динамика учебной выручки, январь–март 2025")
plt.xlabel("Месяц")
plt.ylabel("Выручка, руб.")
plt.grid(alpha=0.25)
plt.tight_layout()
plt.show()
print("Итог: в феврале выручка снизилась относительно января,")
print("а в марте выросла относительно февраля; ведущая категория —", category_revenue.index[0])
print("Ограничения: есть лишь три месяца наблюдений; нет данных о себестоимости,")
print("расходах и причинах изменений. Выручка не равна прибыли.")
print("Рекомендация: изучить более продолжительный период и факторы")
print("формирования продаж, прежде чем объяснять колебания.")
$python$)
)
INSERT INTO exercise_answers (lesson_id, exercise_id, answer)
SELECT 14, solutions.exercise_id,
    json_build_object('type', 'code', 'language', 'python', 'check_mode', 'graded',
        'value', $prefix$import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO

csv_text = """$prefix$ || dataset.csv || E'"""\n\n' || solutions.body)::text
FROM solutions CROSS JOIN dataset
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer, updated_at = NOW();
