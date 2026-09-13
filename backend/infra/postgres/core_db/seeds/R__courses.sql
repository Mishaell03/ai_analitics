-- =========================================================
-- COURSES
-- =========================================================

INSERT INTO courses (
    slug,
    title,
    description,
    is_published
) VALUES
(
    'ai-development-beginner',
    'AI-разработка: Начальный уровень',
    'Первые шаги в мире искусственного интеллекта. Изучите основы Python, работу с данными, принципы машинного обучения и создайте свои первые AI-приложения.',
    TRUE
),
(
    'ai-development-intermediate',
    'AI-разработка: Средний уровень',
    'Перейдите от базовых знаний к созданию полноценных AI-систем. Освойте нейронные сети, работу с LLM, RAG, векторные базы данных и интеграцию моделей в реальные приложения.',
    TRUE
),
(
    'ai-development-master',
    'AI-разработка: Master',
    'Глубокое погружение в современную AI-разработку. Проектируйте production-ready AI-системы, создавайте интеллектуальных агентов, оптимизируйте модели и объединяйте LLM, RAG и собственные ML-компоненты в масштабируемые решения.',
    TRUE
);


-- =========================================================
-- BEGINNER
-- =========================================================

-- Module 1
INSERT INTO course_modules (
    course_id,
    title,
    description,
    position
) VALUES (
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-beginner'
    ),
    'Основы Python для AI',
    'Изучите Python и основные инструменты, необходимые для дальнейшей работы с искусственным интеллектом.',
    1
);

-- Module 2
INSERT INTO course_modules (
    course_id,
    title,
    description,
    position
) VALUES (
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-beginner'
    ),
    'Основы машинного обучения',
    'Познакомьтесь с ключевыми концепциями машинного обучения и создайте свою первую ML-модель.',
    2
);


-- Lessons Module 1
INSERT INTO lessons (
    module_id,
    title,
    description,
    position
) VALUES
(
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
    'Python: переменные, типы данных и функции',
    'Разберитесь с базовыми типами данных Python, переменными, условиями, циклами и функциями. Напишите первые небольшие программы.',
    1
),
(
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
    2
);


-- Lessons Module 2
INSERT INTO lessons (
    module_id,
    title,
    description,
    position
) VALUES
(
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
);


-- =========================================================
-- INTERMEDIATE
-- =========================================================

-- Module 1
INSERT INTO course_modules (
    course_id,
    title,
    description,
    position
) VALUES (
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-intermediate'
    ),
    'Нейронные сети',
    'Изучите устройство нейронных сетей, процесс обучения и основные архитектуры глубокого обучения.',
    1
);

-- Module 2
INSERT INTO course_modules (
    course_id,
    title,
    description,
    position
) VALUES (
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-intermediate'
    ),
    'LLM и RAG',
    'Познакомьтесь с большими языковыми моделями и создайте систему генерации ответов на основе собственных данных.',
    2
);


-- Lessons Module 1
INSERT INTO lessons (
    module_id,
    title,
    description,
    position
) VALUES
(
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
);


-- Lessons Module 2
INSERT INTO lessons (
    module_id,
    title,
    description,
    position
) VALUES
(
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
);


-- =========================================================
-- MASTER
-- =========================================================

-- Module 1
INSERT INTO course_modules (
    course_id,
    title,
    description,
    position
) VALUES (
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-master'
    ),
    'AI-агенты',
    'Научитесь проектировать интеллектуальных агентов, способных использовать инструменты, планировать действия и выполнять сложные задачи.',
    1
);

-- Module 2
INSERT INTO course_modules (
    course_id,
    title,
    description,
    position
) VALUES (
    (
        SELECT course_id
        FROM courses
        WHERE slug = 'ai-development-master'
    ),
    'Production AI-системы',
    'Разберитесь с архитектурой production-ready AI-систем, оптимизацией моделей, мониторингом и масштабированием.',
    2
);


-- Lessons Module 1
INSERT INTO lessons (
    module_id,
    title,
    description,
    position
) VALUES
(
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
);


-- Lessons Module 2
INSERT INTO lessons (
    module_id,
    title,
    description,
    position
) VALUES
(
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
);