"""Output-based chart checks and expert-access policy for lessons 13–14."""

import math

CATEGORY_VALUES = {
    "Электроника": 220000,
    "Аксессуары": 37500,
    "Бытовая техника": 34700,
    "Канцелярия": 5540,
    "Товары для дома": 5040,
}
MONTH_VALUES = {"2025-01": 129950, "2025-02": 55310, "2025-03": 117520}
CHART_EXERCISES = frozenset(f"lesson_13_python_{number:02d}" for number in range(1, 4))


def is_chart_exercise(lesson_id: int, exercise_id: str) -> bool:
    return (lesson_id == 13 and exercise_id in CHART_EXERCISES) or (
        lesson_id == 14 and exercise_id in {f"lesson_14_python_{n:02d}" for n in range(1, 4)}
    )


def grade_chart(execution, exercise_id: str) -> tuple[bool, str | None]:
    if not execution.success:
        return False, "Исправьте ошибку выполнения и запустите программу ещё раз."
    if not execution.plots:
        return False, "График не получен. Постройте диаграмму и вызовите plt.show(). Если вызов уже есть, обновите и перезапустите sandbox runner."
    if not execution.chart_data or len(execution.chart_data) != len(execution.plots):
        return False, "Runner не передал данные диаграммы для проверки. Обновите и перезапустите sandbox runner."
    monthly = exercise_id in {"lesson_13_python_02", "lesson_14_python_03"}
    expected = MONTH_VALUES if monthly else CATEGORY_VALUES
    for figure in execution.chart_data:
        for series in figure["series"]:
            if series["kind"] != ("line" if monthly else "bar"):
                continue
            labels = [label[:7] if monthly else label for label in series["labels"]]
            values = series["values"]
            if len(labels) != len(expected) or len(set(labels)) != len(expected) or set(labels) != set(expected):
                continue
            if any(not math.isclose(value, expected[label], rel_tol=1e-8, abs_tol=0.01)
                   for label, value in zip(labels, values)):
                continue
            if monthly and labels != list(MONTH_VALUES):
                continue
            if not monthly and (not series["zero_baseline"] or (
                    exercise_id.startswith("lesson_13_") and values != sorted(values, reverse=True))):
                continue
            if not all(series[key].strip() for key in ("title", "xlabel", "ylabel")):
                return False, "Добавьте заголовок графика и подписи обеих осей с единицами измерения."
            return True, None
    return False, ("Проверьте тип графика, подписи категорий/месяцев, значения выручки и сортировку. "
                   "Для столбцов числовая ось должна начинаться с нуля.")
