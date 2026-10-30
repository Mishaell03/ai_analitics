"""Technical checks for project outputs; the teacher's 10-point grade is manual."""

import re
from decimal import Decimal

from app.services.sandbox.chart_grading import CATEGORY_VALUES, grade_chart


def metric(text, label, expected):
    matches = re.findall(r"^" + re.escape(label) + r":\s*(-?\d+(?:[.,]\d+)?)\s*$", text, re.M)
    return len(matches) == 1 and Decimal(matches[0].replace(",", ".")) == Decimal(str(expected))


def grade_project(execution, exercise_id):
    if not execution.success:
        return False, "Исправьте ошибку выполнения и запустите программу ещё раз."
    text = execution.stdout
    if exercise_id.endswith("01"):
        checks = {
            "Повторяющиеся уникальные line_item_id": 0,
            "Разных заказов среди всех статусов": 20,
            "Отменённых позиций": 4,
            "Количество <= 0": 0,
            "Отрицательных цен": 0,
            "Неожиданных статусов": 0,
            "Завершённых товарных позиций": 32,
            "Уникальных завершённых заказов": 17,
            "Продано единиц": 62,
            "Учебная выручка, руб.": 302780,
        }
        if not re.search(r"Размер таблицы \(строки, столбцы\):\s*\(36,\s*9\)", text):
            return False, "Проверьте размер исходной таблицы и подпись контрольного показателя."
        if not re.search(r"Отменённые ID:\s*\[7,\s*17,\s*18,\s*29\]", text):
            return False, "Проверьте отбор отменённых позиций и выведите их ID."
        for column in ("line_item_id", "order_id", "order_date", "customer_id", "product", "category", "quantity", "unit_price", "status"):
            if not re.search(r"^" + column + r"\s+0\s*$", text, re.M):
                return False, "Выведите количество пропусков по каждому исходному столбцу."
        if not re.search(r"^\s*\d+\s+28\s+1(?:\.0+)?\s+0(?:\.0+)?\s*$", text, re.M):
            return False, "Покажите бесплатную завершённую позицию со столбцами line_item_id, quantity, unit_price."
    else:
        passed, feedback = grade_chart(execution, exercise_id)
        if not passed:
            return passed, feedback
        if exercise_id.endswith("02"):
            checks = {"Общая завершённая выручка, руб.": 302780, "Итог категорий, руб.": 302780}
            units = {"Электроника": 5, "Аксессуары": 13, "Бытовая техника": 7, "Канцелярия": 24, "Товары для дома": 13}
            for category, revenue in CATEGORY_VALUES.items():
                pattern = r"^" + re.escape(category) + rf"\s+{units[category]}(?:\.0+)?\s+{revenue}(?:\.0+)?\s*$"
                if not re.search(pattern, text, re.M):
                    return False, "Проверьте сводку quantity и line_revenue по всем пяти категориям."
            if "Лидер по выручке: Электроника" not in text or "Лидер по количеству единиц: Канцелярия" not in text:
                return False, "Выведите вычисленных лидеров по выручке и количеству единиц."
            if "Итоги совпадают: True" not in text:
                return False, "Выведите результат сравнения общего итога и суммы категорий."
        else:
            checks = {"Изменение февраль минус январь, руб.": -74640,
                      "Изменение март минус февраль, руб.": 62210,
                      "Общий итог, руб.": 302780, "Сумма месяцев, руб.": 302780}
            if "Суммы совпадают: True" not in text:
                return False, "Выведите результат сравнения общего итога и суммы месяцев."
    for label, value in checks.items():
        if not metric(text, label, value):
            return False, f"Проверьте показатель «{label}» и выведите его отдельной строкой с этой подписью."
    return True, None
