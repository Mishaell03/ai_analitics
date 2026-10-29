-- Урок 4: административные ответы, не включать в студенческий Markdown.
-- course-content/1/1/4.md: номера вариантов 2, 4, 1, 3, 4, 2.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (4, 'lesson_04_test_01', '{"type":"choice","correct":["Текст `2 + 3`."]}'),
    (4, 'lesson_04_test_02', '{"type":"choice","correct":["720"]}'),
    (4, 'lesson_04_test_03', '{"type":"choice","correct":["15"]}'),
    (4, 'lesson_04_test_04', '{"type":"choice","correct":["4.0"]}'),
    (4, 'lesson_04_test_05', '{"type":"choice","correct":["Возникнет ошибка несовместимых типов при сложении."]}'),
    (4, 'lesson_04_test_06', '{"type":"choice","correct":["`Итого: 540`"]}')
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();

-- Эталоны проверены локальным Python, не sandbox. duration=0 — служебное
-- значение, а не замер времени sandbox. Проверка сравнивает stdout, не код.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer)
SELECT 4, seed.exercise_id,
    json_build_object(
        'type', 'code', 'language', 'python', 'value', seed.code,
        'execution', json_build_object(
            'stdout', seed.stdout, 'stderr', '', 'exit_code', 0,
            'timed_out', false, 'duration', 0,
            'output_limited', false, 'memory_limited', false
        )
    )::text
FROM (VALUES
    ('lesson_04_python_intro', $python$print("Привет, мир!")
$python$, E'Привет, мир!\n'),
    ('lesson_04_python_01', $python$quantity = 4
unit_price = 275

revenue = quantity * unit_price
print("Выручка:", revenue)

quantity = 6

new_revenue = quantity * unit_price
print("Новая выручка:", new_revenue)
$python$, E'Выручка: 1100\nНовая выручка: 1650\n'),
    ('lesson_04_python_02', $python$bottle_quantity = 2
bottle_price = 900

notebook_quantity = 5
notebook_price = 180

bottle_revenue = bottle_quantity * bottle_price
notebook_revenue = notebook_quantity * notebook_price

difference = bottle_revenue - notebook_revenue

print("Bottle:", bottle_revenue)
print("Notebook:", notebook_revenue)
print("Разница:", difference)
$python$, E'Bottle: 1800\nNotebook: 900\nРазница: 900\n'),
    ('lesson_04_python_03', $python$bottle_completed_quantity = 2
bottle_completed_price = 900

notebook_completed_quantity = 5
notebook_completed_price = 180

bottle_cancelled_quantity = 1
bottle_cancelled_price = 900

completed_revenue = (
    bottle_completed_quantity * bottle_completed_price
    + notebook_completed_quantity * notebook_completed_price
)

all_revenue = (
    completed_revenue
    + bottle_cancelled_quantity * bottle_cancelled_price
)

print("Выручка завершённых:", completed_revenue)
print("С отменённой позицией:", all_revenue)
print("Завышение:", all_revenue - completed_revenue)
$python$, E'Выручка завершённых: 2700\nС отменённой позицией: 3600\nЗавышение: 900\n')
) AS seed(exercise_id, code, stdout)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();
