-- Course 1, module 3, lesson 9: course-content/1/3/9.md.
-- The exercise IDs are stable labels and intentionally do not encode lesson_id.
-- Correct option numbers: 2, 4, 1, 3, 2, 2.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (9, 'pandas_revenue_test_01', '{"type":"choice","correct":["900 и 540."]}'),
    (9, 'pandas_revenue_test_02', '{"type":"choice","correct":["Сначала отобрать `status == \"completed\"`, затем рассчитать и сложить `line_revenue`."]}'),
    (9, 'pandas_revenue_test_03', '{"type":"choice","correct":["1890."]}'),
    (9, 'pandas_revenue_test_04', '{"type":"choice","correct":["Для `Home` — 1350, для `Stationery` — 540."]}'),
    (9, 'pandas_revenue_test_05', '{"type":"choice","correct":["Категории расположатся по убыванию выручки, а значения сумм сохранятся."]}'),
    (9, 'pandas_revenue_test_06', '{"type":"choice","correct":["В общий итог ошибочно включили отменённую позицию, а при группировке её исключили."]}')
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();
