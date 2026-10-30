-- Ответы и эталоны урока 6; код эталонов хранится только в БД.
-- course-content/1/2/6.md: номера вариантов 3, 2, 1, 2, 3, 2.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (6, 'lesson_06_test_01', '{"type":"choice","correct":["`7`"]}'),
    (6, 'lesson_06_test_02', '{"type":"choice","correct":["`3`"]}'),
    (6, 'lesson_06_test_03', '{"type":"choice","correct":["Сначала `4`, затем `6` на новой строке."]}'),
    (6, 'lesson_06_test_04', '{"type":"choice","correct":["`11`"]}'),
    (6, 'lesson_06_test_05', '{"type":"choice","correct":["`2`"]}'),
    (6, 'lesson_06_test_06', '{"type":"choice","correct":["Будет выведено `6`, потому что `total` обнуляется на каждом шаге."]}')
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();

-- Эталоны сверяются по stdout; duration=0 — служебное, не замер sandbox.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer)
SELECT 6, seed.exercise_id,
    json_build_object(
        'type', 'code', 'language', 'python', 'value', seed.code,
        'execution', json_build_object(
            'stdout', seed.stdout, 'stderr', '', 'exit_code', 0,
            'timed_out', false, 'duration', 0,
            'output_limited', false, 'memory_limited', false
        )
    )::text
FROM (VALUES
    ('lesson_06_python_01', $python$quantities = [3, 2, 4, 1]
total_quantity = 0

for quantity in quantities:
    total_quantity = total_quantity + quantity

print("Всего единиц:", total_quantity)
print("Число позиций:", len(quantities))
$python$, E'Всего единиц: 10\nЧисло позиций: 4\n'),
    ('lesson_06_python_02', $python$statuses = ["completed", "cancelled", "completed", "processing", "cancelled", "completed"]

completed_count = 0
cancelled_count = 0
unknown_count = 0

for status in statuses:
    if status == "completed":
        completed_count = completed_count + 1
    elif status == "cancelled":
        cancelled_count = cancelled_count + 1
    else:
        unknown_count = unknown_count + 1

print("Завершённых:", completed_count)
print("Отменённых:", cancelled_count)
print("Неизвестных:", unknown_count)
$python$, E'Завершённых: 3\nОтменённых: 2\nНеизвестных: 1\n'),
    ('lesson_06_python_03', $python$items = [
    ["completed", 2, 900],
    ["completed", 5, 180],
    ["cancelled", 1, 900],
    ["completed", 1, 450],
    ["processing", 2, 300],
]

total_revenue = 0
completed_count = 0
cancelled_count = 0
unknown_count = 0

for item in items:
    status = item[0]
    quantity = item[1]
    unit_price = item[2]

    if status == "completed":
        total_revenue = total_revenue + quantity * unit_price
        completed_count = completed_count + 1
    elif status == "cancelled":
        cancelled_count = cancelled_count + 1
    else:
        unknown_count = unknown_count + 1
        print("Неизвестный статус:", status)

print("Учебная выручка:", total_revenue)
print("Завершённых:", completed_count)
print("Отменённых:", cancelled_count)
print("Неизвестных:", unknown_count)
$python$, E'Неизвестный статус: processing\nУчебная выручка: 3150\nЗавершённых: 3\nОтменённых: 1\nНеизвестных: 1\n')
) AS seed(exercise_id, code, stdout)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();
