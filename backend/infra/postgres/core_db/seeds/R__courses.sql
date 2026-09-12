INSERT INTO courses (
    slug,
    title,
    description,
    content_path,
    is_published
) VALUES
(
    'ai-development-beginner',
    'AI-разработка: Начальный уровень',
    'Первые шаги в мире искусственного интеллекта. Изучите основы Python, работу с данными, принципы машинного обучения и создайте свои первые AI-приложения.',
    'course-content/1/content.md',
    TRUE
),
(
    'ai-development-intermediate',
    'AI-разработка: Средний уровень',
    'Перейдите от базовых знаний к созданию полноценных AI-систем. Освойте нейронные сети, работу с LLM, RAG, векторные базы данных и интеграцию моделей в реальные приложения.',
    'course-content/2/content.md',
    TRUE
),
(
    'ai-development-master',
    'AI-разработка: Master',
    'Глубокое погружение в современную AI-разработку. Проектируйте production-ready AI-системы, создавайте интеллектуальных агентов, оптимизируйте модели и объединяйте LLM, RAG и собственные ML-компоненты в масштабируемые решения.',
    'course-content/3/content.md',
    TRUE
);