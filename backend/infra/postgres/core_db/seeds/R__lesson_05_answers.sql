-- Ответы и эталоны урока 5; код эталонов хранится только в БД.
-- course-content/1/2/5.md: номера вариантов 2, 4, 1, 3, 4, 2.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (5, 'lesson_05_test_01', '{"type":"choice","correct":["`False`"]}'),
    (5, 'lesson_05_test_02', '{"type":"choice","correct":["Возникнет синтаксическая ошибка из-за использования `=` вместо `==`."]}'),
    (5, 'lesson_05_test_03', '{"type":"choice","correct":["`Исключаем`"]}'),
    (5, 'lesson_05_test_04', '{"type":"choice","correct":["`Проверяем статус`"]}'),
    (5, 'lesson_05_test_05', '{"type":"choice","correct":["`True`"]}'),
    (5, 'lesson_05_test_06', '{"type":"choice","correct":["Программа выведет «Учитываем», хотя статус не равен `completed`."]}')
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();

-- Эталоны проверяются локально при разработке; сравнение в приложении — по stdout.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer)
SELECT 5, seed.exercise_id,
    json_build_object(
        'type', 'code', 'language', 'python', 'value', seed.code,
        'execution', json_build_object(
            'stdout', seed.stdout, 'stderr', '', 'exit_code', 0,
            'timed_out', false, 'duration', 0,
            'output_limited', false, 'memory_limited', false
        )
    )::text
FROM (VALUES
    ('lesson_05_python_01', $python$status = "cancelled"

if status == "completed":
    print("Позиция учитывается")
else:
    print("Позиция не учитывается")

status = "completed"

if status == "completed":
    print("Позиция учитывается")
else:
    print("Позиция не учитывается")
$python$, E'Позиция не учитывается\nПозиция учитывается\n'),
    ('lesson_05_python_02', $python$quantity = 0
unit_price = 900
status = "processing"

values_ok = quantity > 0 and unit_price >= 0
status_ok = status == "completed" or status == "cancelled"

if values_ok:
    print("Количество и цена соответствуют правилам")
else:
    print("Проверьте количество или цену")

if status == "completed":
    print("Статус: завершён")
elif status == "cancelled":
    print("Статус: отменён")
else:
    print("Неизвестный статус")

if values_ok and status_ok:
    print("Запись прошла проверки")
else:
    print("Запись требует проверки")
$python$, E'Проверьте количество или цену\nНеизвестный статус\nЗапись требует проверки\n'),
    ('lesson_05_python_03', $python$# Позиция 2004
quantity_2004 = 2
unit_price_2004 = 900
status_2004 = "completed"

# Позиция 2005
quantity_2005 = 5
unit_price_2005 = 180
status_2005 = "completed"

# Позиция 2006
quantity_2006 = 1
unit_price_2006 = 900
status_2006 = "cancelled"

total_revenue = 0
completed_count = 0

if status_2004 == "completed":
    total_revenue = total_revenue + quantity_2004 * unit_price_2004
    completed_count = completed_count + 1
elif status_2004 != "cancelled":
    print("Неизвестный статус позиции 2004")

if status_2005 == "completed":
    total_revenue = total_revenue + quantity_2005 * unit_price_2005
    completed_count = completed_count + 1
elif status_2005 != "cancelled":
    print("Неизвестный статус позиции 2005")

if status_2006 == "completed":
    total_revenue = total_revenue + quantity_2006 * unit_price_2006
    completed_count = completed_count + 1
elif status_2006 != "cancelled":
    print("Неизвестный статус позиции 2006")

print("Учебная выручка:", total_revenue)
print("Учтено завершённых позиций:", completed_count)
$python$, E'Учебная выручка: 2700\nУчтено завершённых позиций: 2\n')
) AS seed(exercise_id, code, stdout)
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();

-- Иллюстрация неизвестного статуса в уроке 5.
INSERT INTO media_files (
    media_key, course_id, object_key, kind, content_type, size_bytes,
    width, height, original_name
) VALUES (
    'm_72e62512f7eb46e3', 1, '1/media/m_72e62512f7eb46e3.png',
    'image', 'image/png', 248238, 1122, 1402, 'm_72e62512f7eb46e3.png'
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
SELECT 5, media_id
FROM media_files
WHERE media_key = 'm_72e62512f7eb46e3' AND course_id = 1
ON CONFLICT (lesson_id, media_id) DO NOTHING;
