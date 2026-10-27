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
            (1, 1, 1), (2, 1, 2), (3, 2, 1),
            (4, 2, 2), (5, 3, 1), (6, 3, 2)
        ) AS seed(module_id, course_id, position)
            ON m.module_id = seed.module_id
            OR (m.course_id = seed.course_id AND m.position = seed.position)
        WHERE m.module_id <> seed.module_id
            OR m.course_id <> seed.course_id OR m.position <> seed.position
    ) OR EXISTS (
        SELECT 1
        FROM lessons l
        JOIN (VALUES
            (1, 1, 1), (2, 1, 2), (3, 2, 1), (4, 2, 2),
            (5, 3, 1), (6, 3, 2), (7, 4, 1), (8, 4, 2),
            (9, 5, 1), (10, 5, 2), (11, 6, 1), (12, 6, 2)
        ) AS seed(lesson_id, module_id, position)
            ON l.lesson_id = seed.lesson_id
            OR (l.module_id = seed.module_id AND l.position = seed.position)
        WHERE l.lesson_id <> seed.lesson_id
            OR l.module_id <> seed.module_id OR l.position <> seed.position
    ) THEN
        RAISE EXCEPTION 'Seed IDs conflict with existing courses/modules/lessons; MinIO paths require fixed IDs. No existing records were remapped.';
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
    'AI-разработка: Начальный уровень',
    'Освойте анализ данных с нуля! Научитесь работать с Python, pandas и SQL, обрабатывать таблицы, находить закономерности и визуализировать результаты.

Вас ждут понятные объяснения, практические задания и реальные бизнес-кейсы. К концу курса вы сможете самостоятельно анализировать данные, проверять расчёты и делать обоснованные выводы.

**Подходит новичкам без опыта программирования.**',
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
    'Основы Python для AI',
    'Изучите Python и основные инструменты, необходимые для дальнейшей работы с искусственным интеллектом.',
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
    2,
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-beginner'
    ),
    'Основы машинного обучения',
    'Познакомьтесь с ключевыми концепциями машинного обучения и создайте свою первую ML-модель.',
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
    'От бизнес-запроса к аналитической задаче',
    'Научитесь формулировать аналитические вопросы, выбирать метрики, рассчитывать учебную выручку и обосновывать выводы по данным.',
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
    'Работа с данными в Python',
    'Познакомьтесь со списками, словарями и таблицами данных. Научитесь загружать, преобразовывать и анализировать данные.',
    2,
    TRUE
)
ON CONFLICT (lesson_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    is_published = TRUE,
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
    3,
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
    'Что такое машинное обучение',
    'Изучите основные понятия машинного обучения, типы задач и разницу между обучением с учителем и без учителя.',
    1
),
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
    'Первая ML-модель',
    'Создайте первую модель машинного обучения, подготовьте данные, обучите модель и оцените качество её предсказаний.',
    2
)
ON CONFLICT (lesson_id) DO UPDATE SET
    title = EXCLUDED.title,
    description = EXCLUDED.description,
    updated_at = NOW();


-- =========================================================
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
    3,
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
    4,
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
    5,
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
    6,
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
    7,
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
    8,
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
    5,
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
    9,
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
    10,
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
    11,
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
    12,
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

-- course-content/1/1/1.md: номера верных вариантов 2, 3, 4, 2, 2, 1.
-- Backend сравнивает choice-ответы по текстам вариантов в JSON.
INSERT INTO exercise_answers (lesson_id, exercise_id, answer) VALUES
    (1, 'lesson_01_test_01', '{"type":"choice","correct":["Уточнить показатель, период и основу сравнения."]}'),
    (1, 'lesson_01_test_02', '{"type":"choice","correct":["Одну товарную позицию заказа с заданным количеством."]}'),
    (1, 'lesson_01_test_03', '{"type":"choice","correct":["Суммировать `quantity × unit_price` только для `completed`."]}'),
    (1, 'lesson_01_test_04', '{"type":"choice","correct":["7 заказов, по числу разных `order_id`."]}'),
    (1, 'lesson_01_test_05', '{"type":"choice","correct":["Home имеет наибольшую учебную выручку в выборке."]}'),
    (1, 'lesson_01_test_06', '{"type":"choice","correct":["Во втором периоде выручка ниже на 540 рублей; причина неизвестна."]}'),
    -- course-content/1/1/2.md: номера верных вариантов 2, 3, 1, 4, 2, 3.
    (2, 'lesson_02_test_01', '{"type":"choice","correct":["10 строк данных и 9 столбцов."]}'),
    (2, 'lesson_02_test_02', '{"type":"choice","correct":["Один заказ содержит две товарные позиции."]}'),
    (2, 'lesson_02_test_03', '{"type":"choice","correct":["В CSV это текст, который программа может распознать как дату."]}'),
    (2, 'lesson_02_test_04', '{"type":"choice","correct":["Чтобы запятая внутри названия не разделяла поле."]}'),
    (2, 'lesson_02_test_05', '{"type":"choice","correct":["Зафиксировать повтор уникального ключа и уточнить источник."]}'),
    (2, 'lesson_02_test_06', '{"type":"choice","correct":["Проверить пропуски, числовые правила и согласованность статусов."]}')
ON CONFLICT (lesson_id, exercise_id) DO UPDATE SET
    answer = EXCLUDED.answer,
    updated_at = NOW();
