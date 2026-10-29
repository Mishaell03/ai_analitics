-- =========================================================
-- COURSES
-- =========================================================

-- ID совпадают с каталогами backend/infra/minio/seeds/course-content.
-- При несовместимой раскладке существующей БД не перезаписываем чужие записи.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1
        FROM courses c
        JOIN (VALUES
            (1, 'ai-development-beginner'),
            (2, 'ai-development-intermediate'),
            (3, 'ai-development-master')
        ) AS seed(course_id, slug)
            ON c.course_id = seed.course_id OR c.slug = seed.slug
        WHERE c.course_id <> seed.course_id OR c.slug <> seed.slug
    ) OR EXISTS (
        SELECT 1
        FROM course_modules m
        JOIN (VALUES
            (1, 1, 1), (2, 1, 2), (3, 1, 3), (8, 2, 1),
            (4, 1, 4), (5, 1, 5), (9, 2, 2), (10, 3, 1), (6, 3, 2)
        ) AS seed(module_id, course_id, position)
            ON m.module_id = seed.module_id
            OR (m.course_id = seed.course_id AND m.position = seed.position)
        WHERE m.module_id <> seed.module_id
            OR m.course_id <> seed.course_id OR m.position <> seed.position
    ) OR EXISTS (
        SELECT 1
        FROM lessons l
        JOIN (VALUES
            (1, 1, 1), (2, 1, 2), (3, 1, 3),
            (4, 2, 1), (5, 2, 2), (6, 2, 3),
            (7, 3, 1), (8, 3, 2), (9, 3, 3), (10, 3, 4),
            (18, 8, 1), (19, 8, 2),
            (17, 10, 1), (20, 10, 2), (21, 6, 1), (22, 6, 2),
            (23, 9, 1), (15, 9, 2), (11, 4, 1), (12, 4, 2),
            (13, 5, 1), (14, 5, 2)
        ) AS seed(lesson_id, module_id, position)
            ON l.lesson_id = seed.lesson_id
            OR (l.module_id = seed.module_id AND l.position = seed.position)
        WHERE l.lesson_id <> seed.lesson_id
            OR l.module_id <> seed.module_id OR l.position <> seed.position
    ) THEN
        RAISE EXCEPTION 'Seed IDs conflict with existing courses/modules/lessons; inspect mappings before applying seeds.';
    END IF;
END;
$$;

INSERT INTO courses (
    course_id,
    slug,
    title,
    description,
    is_published
) VALUES
(
    1,
    'ai-development-beginner',
    'Аналитика данных с нуля',
    'Научитесь работать с данными, использовать Python, pandas и SQL, строить графики и делать обоснованные выводы на примере интернет-магазина «Северный свет». Курс начинается с основ и постепенно переходит к практическому анализу.',
    TRUE
),
(
    2,
    'ai-development-intermediate',
    'AI-разработка: Средний уровень',
    'Перейдите от базовых знаний к созданию полноценных AI-систем. Освойте нейронные сети, работу с LLM, RAG, векторные базы данных и интеграцию моделей в реальные приложения.',
    TRUE
),
(
    3,
    'ai-development-master',
    'AI-разработка: Master',
    'Глубокое погружение в современную AI-разработку. Проектируйте production-ready AI-системы, создавайте интеллектуальных агентов, оптимизируйте модели и объединяйте LLM, RAG и собственные ML-компоненты в масштабируемые решения.',
    TRUE
)
ON CONFLICT (course_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_published = TRUE,
    updated_at = NOW();


-- =========================================================
-- BEGINNER
-- =========================================================

-- Module 1
INSERT INTO course_modules (
    module_id,
    course_id,
    title,
    description,
    position,
    is_published
) VALUES (
    1,
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-beginner'
    ),
    'Модуль 1. Введение в аналитику данных',
    'Познакомьтесь с задачами аналитика, основами работы с данными и ключевыми понятиями анализа.',
    1,
    TRUE
)
ON CONFLICT (module_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_published = TRUE,
    updated_at = NOW();

-- Module 3 of the beginner course: pandas analytics.
INSERT INTO course_modules (
    module_id, course_id, title, description, position, is_published
) VALUES (
    3,
    (SELECT course_id FROM courses WHERE slug = 'ai-development-beginner'),
    'Модуль 3. Обработка и анализ данных с помощью pandas',
    'Научитесь загружать таблицы, исследовать данные, находить ошибки, фильтровать и сортировать записи, рассчитывать показатели и группировать результаты с помощью библиотеки pandas.',
    3,
    TRUE
)
ON CONFLICT (module_id) DO UPDATE SET
    course_id = EXCLUDED.course_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    position = EXCLUDED.position,
    is_published = TRUE,
    updated_at = NOW();

-- Module 2
INSERT INTO course_modules (
    module_id,
    course_id,
    title,
    description,
    position,
    is_published
) VALUES (
    2,
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-beginner'
    ),
    'Модуль 2. Основы Python для аналитики',
    'Освойте базовые конструкции Python и научитесь применять их для простых расчётов и анализа данных.',
    2,
    TRUE
)
ON CONFLICT (module_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_published = TRUE,
    updated_at = NOW();


-- Lessons Module 1
INSERT INTO lessons (
    lesson_id,
    module_id,
    title,
    description,
    position,
    is_published
) VALUES
(
    1,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-beginner'
        )
        AND position = 1
    ),
    'Урок 1. Добро пожаловать на курс «Аналитика данных с нуля»',
    'Вводное видео и знакомство с курсом: данные, Python, pandas, SQL и учебный кейс магазина «Северный свет».',
    1,
    TRUE
),
(
    2,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-beginner'
        )
        AND position = 1
    ),
    'Урок 2. Первые шаги в аналитике данных',
    'Разберитесь, что такое данные и аналитические вопросы, научитесь выбирать метрики и проверять простые расчёты.',
    2,
    TRUE
)
ON CONFLICT (lesson_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_published = TRUE,
    updated_at = NOW();


-- Module 1 continues with the lesson on tabular data and CSV.
INSERT INTO lessons (lesson_id, module_id, title, description, position, is_published)
VALUES (
    3, 1,
    'Урок 3. Табличные данные: строки, столбцы, типы данных и CSV',
    'Изучите структуру таблиц и CSV, типы значений, идентификаторы и базовые проверки качества данных.',
    3, TRUE
)
ON CONFLICT (lesson_id) DO UPDATE SET
    module_id = EXCLUDED.module_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    position = EXCLUDED.position,
    is_published = TRUE,
    updated_at = NOW();

-- Lessons Module 2: Python fundamentals, matching course-content/1/2/4–6.md.
INSERT INTO lessons (
    lesson_id,
    module_id,
    title,
    description,
    position,
    is_published
) VALUES
(
    4,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-beginner'
        )
        AND position = 2
    ),
    'Урок 4. Python с нуля: первые команды, переменные и вычисления',
    'Познакомьтесь с print(), переменными, типами данных и арифметическими вычислениями на Python.',
    1,
    TRUE
),
(
    5,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-beginner'
        )
        AND position = 2
    ),
    'Урок 5. Условия в Python: if, elif, else и логические проверки',
    'Научитесь проверять значения и статусы с помощью условий и логических операторов.',
    2,
    TRUE
),
(
    6,
    (
        SELECT module_id FROM course_modules
        WHERE course_id = (SELECT course_id FROM courses WHERE slug = 'ai-development-beginner')
            AND position = 2
    ),
    'Урок 6. Списки и циклы в Python: обработка нескольких записей',
    'Освойте списки, циклы for, накопители и обработку нескольких записей с учётом статусов.',
    3,
    TRUE
)
ON CONFLICT (lesson_id) DO UPDATE SET
    module_id = EXCLUDED.module_id,
    position = EXCLUDED.position,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_published = TRUE,
    updated_at = NOW();

-- Beginner course lessons 7–8 occupy the established content IDs and paths.
INSERT INTO lessons (lesson_id, module_id, title, description, position, is_published)
VALUES (
    7,
    3,
    'Урок 7. Первое знакомство с pandas: загрузка CSV и исследование таблицы',
    'Научитесь загружать таблицы, исследовать структуру, типы данных и пропуски до начала анализа.',
    1,
    TRUE
)
ON CONFLICT (lesson_id) DO UPDATE SET
    module_id = EXCLUDED.module_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    position = EXCLUDED.position,
    is_published = TRUE,
    updated_at = NOW();

INSERT INTO lessons (lesson_id, module_id, title, description, position, is_published)
VALUES (
    8,
    3,
    'Урок 8. Фильтрация и сортировка данных в pandas',
    'Научитесь выбирать записи по нескольким условиям, оставлять нужные столбцы и сортировать результаты для ответа на аналитический вопрос.',
    2,
    TRUE
)
ON CONFLICT (lesson_id) DO UPDATE SET
    module_id = EXCLUDED.module_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    position = EXCLUDED.position,
    is_published = TRUE,
    updated_at = NOW();

INSERT INTO lessons (lesson_id, module_id, title, description, position, is_published)
VALUES (
    9,
    3,
    'Урок 9. Расчёт показателей и группировка данных в pandas',
    'Научитесь рассчитывать выручку позиций, группировать показатели по категориям, сортировать результаты и проверять согласованность итогов.',
    3,
    TRUE
)
ON CONFLICT (lesson_id) DO UPDATE SET
    module_id = EXCLUDED.module_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    position = EXCLUDED.position,
    is_published = TRUE,
    updated_at = NOW();


INSERT INTO lessons (lesson_id, module_id, title, description, position, is_published)
VALUES (
    10, 3,
    'Урок 10. Качество данных и основы описательной статистики',
    'Научитесь находить пропуски и повторы идентификаторов, проверять бизнес-правила и рассчитывать описательную статистику по проверенным данным.',
    4, TRUE
)
ON CONFLICT (lesson_id) DO UPDATE SET
    module_id = EXCLUDED.module_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    position = EXCLUDED.position,
    is_published = TRUE,
    updated_at = NOW();

-- Course 1: module 4 and lesson 11, matching course-content/1/4/11.md.
INSERT INTO course_modules (module_id, course_id, title, description, position, is_published)
VALUES (4, 1, 'Модуль 4. Основы SQL для аналитики',
    'Научитесь выбирать и фильтровать записи, сортировать результаты и рассчитывать показатели в учебной базе PostgreSQL.', 4, TRUE)
ON CONFLICT (module_id) DO UPDATE SET
    title = EXCLUDED.title, description = EXCLUDED.description,
    is_published = TRUE, updated_at = NOW();

INSERT INTO lessons (lesson_id, module_id, title, description, position, is_published)
VALUES (11, 4, 'Урок 11. Основы SQL: первые запросы к базе данных',
    'Освойте SELECT, WHERE, ORDER BY, LIMIT, COUNT и SUM на данных магазина «Северный свет».', 1, TRUE)
ON CONFLICT (lesson_id) DO UPDATE SET
    title = EXCLUDED.title, description = EXCLUDED.description,
    is_published = TRUE, updated_at = NOW();

INSERT INTO lessons (lesson_id, module_id, title, description, position, is_published)
VALUES (12, 4, 'Урок 12. Группировка и объединение таблиц в SQL',
    'Научитесь строить сводные показатели с GROUP BY, объединять таблицы через INNER JOIN и проверять итоги на наборе розничных продаж.', 2, TRUE)
ON CONFLICT (lesson_id) DO UPDATE SET
    module_id = EXCLUDED.module_id, position = EXCLUDED.position,
    title = EXCLUDED.title, description = EXCLUDED.description,
    is_published = TRUE, updated_at = NOW();

INSERT INTO course_modules (module_id, course_id, title, description, position, is_published)
VALUES (5, 1, 'Модуль 5. Визуализация и итоговый проект',
    'Постройте наглядные графики и подготовьте итоговый аналитический отчёт по данным розничных продаж.', 5, TRUE)
ON CONFLICT (module_id) DO UPDATE SET
    title = EXCLUDED.title, description = EXCLUDED.description,
    course_id = EXCLUDED.course_id, position = EXCLUDED.position,
    is_published = TRUE, updated_at = NOW();

INSERT INTO lessons (lesson_id, module_id, title, description, position, is_published)
VALUES (13, 5, 'Урок 13. Визуализация данных с помощью matplotlib',
    'Постройте графики категорий и месяцев на настоящих данных RETAIL SALES, проверьте расчёты и сформулируйте выводы без недоказанных причин.', 1, TRUE)
ON CONFLICT (lesson_id) DO UPDATE SET
    title = EXCLUDED.title, description = EXCLUDED.description,
    module_id = EXCLUDED.module_id, position = EXCLUDED.position,
    is_published = TRUE, updated_at = NOW();

INSERT INTO lessons (lesson_id, module_id, title, description, position, is_published)
VALUES (14, 5, 'Урок 14. Итоговый аналитический проект: исследование продаж интернет-магазина',
    'Проверьте данные RETAIL SALES, рассчитайте показатели, сравните категории и месяцы и подготовьте обоснованный аналитический вывод.', 2, TRUE)
ON CONFLICT (lesson_id) DO UPDATE SET
    title = EXCLUDED.title, description = EXCLUDED.description,
    module_id = EXCLUDED.module_id, position = EXCLUDED.position,
    is_published = TRUE, updated_at = NOW();

-- INTERMEDIATE
-- =========================================================

-- Module 1
INSERT INTO course_modules (
    module_id,
    course_id,
    title,
    description,
    position,
    is_published
) VALUES (
    8,
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-intermediate'
    ),
    'Нейронные сети',
    'Изучите устройство нейронных сетей, процесс обучения и основные архитектуры глубокого обучения.',
    1,
    TRUE
)
ON CONFLICT (module_id) DO UPDATE SET
    course_id = EXCLUDED.course_id,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    position = EXCLUDED.position,
    is_published = TRUE,
    updated_at = NOW();

-- Module 2
INSERT INTO course_modules (
    module_id,
    course_id,
    title,
    description,
    position,
    is_published
) VALUES (
    9,
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-intermediate'
    ),
    'LLM и RAG',
    'Познакомьтесь с большими языковыми моделями и создайте систему генерации ответов на основе собственных данных.',
    2,
    TRUE
)
ON CONFLICT (module_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_published = TRUE,
    updated_at = NOW();


-- Lessons Module 1
INSERT INTO lessons (
    lesson_id,
    module_id,
    title,
    description,
    position
) VALUES
(
    18,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-intermediate'
        )
        AND position = 1
    ),
    'Как работают нейронные сети',
    'Разберите устройство нейрона, слои нейронной сети, функции активации и процесс прямого и обратного распространения ошибки.',
    1
),
(
    19,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-intermediate'
        )
        AND position = 1
    ),
    'Обучение и оптимизация моделей',
    'Изучите функции потерь, градиентный спуск, оптимизаторы и основные способы улучшения качества нейронных сетей.',
    2
)
ON CONFLICT (lesson_id) DO UPDATE SET
    module_id = EXCLUDED.module_id,
    position = EXCLUDED.position,
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    updated_at = NOW();


-- Lessons Module 2
INSERT INTO lessons (
    lesson_id,
    module_id,
    title,
    description,
    position
) VALUES
(
    23,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-intermediate'
        )
        AND position = 2
    ),
    'Большие языковые модели',
    'Разберитесь, как устроены LLM, что такое токены, контекст, трансформеры и генерация текста.',
    1
),
(
    15,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-intermediate'
        )
        AND position = 2
    ),
    'RAG: поиск знаний перед генерацией',
    'Создайте базовую RAG-систему, которая ищет релевантную информацию в документах и передаёт её языковой модели для формирования ответа.',
    2
)
ON CONFLICT (lesson_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    updated_at = NOW();


-- =========================================================
-- MASTER
-- =========================================================

-- Module 1
INSERT INTO course_modules (
    module_id,
    course_id,
    title,
    description,
    position,
    is_published
) VALUES (
    10,
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-master'
    ),
    'AI-агенты',
    'Научитесь проектировать интеллектуальных агентов, способных использовать инструменты, планировать действия и выполнять сложные задачи.',
    1,
    TRUE
)
ON CONFLICT (module_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_published = TRUE,
    updated_at = NOW();

-- Module 2
INSERT INTO course_modules (
    module_id,
    course_id,
    title,
    description,
    position,
    is_published
) VALUES (
    6,
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-master'
    ),
    'Production AI-системы',
    'Разберитесь с архитектурой production-ready AI-систем, оптимизацией моделей, мониторингом и масштабированием.',
    2,
    TRUE
)
ON CONFLICT (module_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_published = TRUE,
    updated_at = NOW();


-- Lessons Module 1
INSERT INTO lessons (
    lesson_id,
    module_id,
    title,
    description,
    position
) VALUES
(
    17,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-master'
        )
        AND position = 1
    ),
    'Архитектура AI-агентов',
    'Изучите основные компоненты AI-агента, циклы принятия решений, память, инструменты и взаимодействие с внешними системами.',
    1
),
(
    20,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-master'
        )
        AND position = 1
    ),
    'Инструменты и планирование агентов',
    'Научитесь подключать инструменты к агентам, строить цепочки действий и организовывать выполнение многошаговых задач.',
    2
)
ON CONFLICT (lesson_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    updated_at = NOW();


-- Lessons Module 2
INSERT INTO lessons (
    lesson_id,
    module_id,
    title,
    description,
    position
) VALUES
(
    21,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-master'
        )
        AND position = 2
    ),
    'Production-ready AI-архитектура',
    'Спроектируйте масштабируемую архитектуру AI-приложения с учётом производительности, отказоустойчивости, безопасности и стоимости.',
    1
),
(
    22,
    (
        SELECT module_id
        FROM course_modules
        WHERE course_id = (
            SELECT course_id
            FROM courses
            WHERE slug = 'ai-development-master'
        )
        AND position = 2
    ),
    'Мониторинг и оптимизация AI-систем',
    'Изучите мониторинг AI-приложений, оценку качества ответов, оптимизацию latency и стоимости, а также контроль работы моделей в production.',
    2
)
ON CONFLICT (lesson_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    updated_at = NOW();

-- Явные ID не продвигают identity-последовательности автоматически.
-- Не уменьшаем уже выданные значения, в том числе после удаления записей.
SELECT setval(pg_get_serial_sequence('courses', 'course_id'),
    GREATEST((SELECT MAX(course_id) FROM courses),
        nextval(pg_get_serial_sequence('courses', 'course_id'))), TRUE);
SELECT setval(pg_get_serial_sequence('course_modules', 'module_id'),
    GREATEST((SELECT MAX(module_id) FROM course_modules),
        nextval(pg_get_serial_sequence('course_modules', 'module_id'))), TRUE);
SELECT setval(pg_get_serial_sequence('lessons', 'lesson_id'),
    GREATEST((SELECT MAX(lesson_id) FROM lessons),
        nextval(pg_get_serial_sequence('lessons', 'lesson_id'))), TRUE);

-- После перестановки уроков удаляем прежние ответы уроков 1 и 2.
DELETE FROM exercise_answers WHERE lesson_id IN (1, 2);

-- course-content/1/1/2.md: номера верных вариантов 3, 2, 1, 4, 2, 3.
-- Backend сравнивает choice-ответы по текстам вариантов в JSON.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (2, 'lesson_02_test_07', '{"type":"choice","correct":["Поиск ответа на вопрос с помощью проверки и обработки данных."]}'),
    (2, 'lesson_02_test_08', '{"type":"choice","correct":["Одну товарную позицию заказа, где может быть несколько единиц."]}'),
    (2, 'lesson_02_test_09', '{"type":"choice","correct":["2"]}'),
    (2, 'lesson_02_test_10', '{"type":"choice","correct":["Потому что по правилам задачи считаются только завершённые позиции."]}'),
    (2, 'lesson_02_test_11', '{"type":"choice","correct":["360 руб."]}'),
    (2, 'lesson_02_test_12', '{"type":"choice","correct":["Уточнить показатель и получить данные за сопоставимый период."]}'),
    -- course-content/1/1/3.md: номера верных вариантов 2, 3, 1, 4, 2, 3.
    (3, 'lesson_03_test_01', '{"type":"choice","correct":["9 записей и 9 столбцов."]}'),
    (3, 'lesson_03_test_02', '{"type":"choice","correct":["Один заказ содержит две товарные позиции."]}'),
    (3, 'lesson_03_test_03', '{"type":"choice","correct":["Это подозрительное повторение уникального идентификатора."]}'),
    (3, 'lesson_03_test_04', '{"type":"choice","correct":["Для расчёта ожидается целое число, а записан текст."]}'),
    (3, 'lesson_03_test_05', '{"type":"choice","correct":["Позиции одного заказа должны относиться к одному клиенту."]}'),
    (3, 'lesson_03_test_06', '{"type":"choice","correct":["Она является частью значения одного поля."]}')
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();

-- Вводное видео урока 1. Ключ совпадает с asset-ссылкой в 1/1/1.md.
-- Сам MP4 загружается в MinIO из infra/minio/seeds/course-content.
INSERT INTO media_files (
    media_key, course_id, object_key, kind, content_type, size_bytes,
    width, height, duration_seconds, video_codec, audio_codec, original_name
) VALUES (
    'm_bb0da2e8512e410c', 1, '1/media/m_bb0da2e8512e410c.mp4',
    'video', 'video/mp4', 3467965,
    1024, 768, 15.104, 'h264', 'aac', 'm_bb0da2e8512e410c.mp4'
)
ON CONFLICT (media_key) DO UPDATE SET
    object_key = EXCLUDED.object_key,
    kind = EXCLUDED.kind,
    content_type = EXCLUDED.content_type,
    size_bytes = EXCLUDED.size_bytes,
    width = EXCLUDED.width,
    height = EXCLUDED.height,
    duration_seconds = EXCLUDED.duration_seconds,
    video_codec = EXCLUDED.video_codec,
    audio_codec = EXCLUDED.audio_codec,
    original_name = EXCLUDED.original_name,
    updated_at = NOW()
WHERE media_files.course_id = EXCLUDED.course_id;

INSERT INTO lesson_media (lesson_id, media_id)
SELECT l.lesson_id, m.media_id
FROM media_files m
JOIN lessons l ON l.lesson_id = 1
JOIN course_modules cm ON cm.module_id = l.module_id
WHERE m.media_key = 'm_bb0da2e8512e410c'
    AND m.course_id = 1 AND cm.course_id = m.course_id
ON CONFLICT (lesson_id, media_id) DO NOTHING;
