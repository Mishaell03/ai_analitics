-- Demo keeps course_id 4. Positions are local to the course/module;
-- technical module_id 11 and lesson_ids 24–25 are globally unique.
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM courses
        WHERE (course_id = 4 OR slug = 'platform-demo')
            AND (course_id <> 4 OR slug <> 'platform-demo')
    ) OR EXISTS (
        SELECT 1 FROM course_modules
        WHERE (module_id = 11 OR (course_id = 4 AND position = 1))
            AND (module_id <> 11 OR course_id <> 4 OR position <> 1)
    ) OR EXISTS (
        SELECT 1 FROM lessons l
        JOIN (VALUES (24, 1), (25, 2)) seed(lesson_id, position)
            ON l.lesson_id = seed.lesson_id OR (l.module_id = 11 AND l.position = seed.position)
        WHERE l.lesson_id <> seed.lesson_id OR l.module_id <> 11 OR l.position <> seed.position
    ) THEN
        RAISE EXCEPTION 'Demo course IDs conflict with existing records; inspect the mapping before seeding.';
    END IF;
END;
$$;

INSERT INTO courses (course_id, slug, title, description, is_published, sort_order)
VALUES (4, 'platform-demo', 'Демонстрация платформы',
    'Краткий видеообзор основных возможностей платформы: обучение, практические задания на Python и SQL, тестирование и AI-наставник.', TRUE, 0)
ON CONFLICT (course_id) DO UPDATE SET
    title = EXCLUDED.title, description = EXCLUDED.description,
    is_published = TRUE, sort_order = EXCLUDED.sort_order, updated_at = NOW();

INSERT INTO course_modules (module_id, course_id, title, description, position, is_published)
VALUES (11, 4, 'Модуль 1. Знакомство с платформой',
    'Посмотрите презентацию проекта и видеообзор обучения, практики и AI-наставника.', 1, TRUE)
ON CONFLICT (module_id) DO UPDATE SET
    title = EXCLUDED.title, description = EXCLUDED.description,
    is_published = TRUE, updated_at = NOW();

INSERT INTO lessons (lesson_id, module_id, title, description, position, is_published) VALUES
    (24, 11, 'Урок 1. Знакомство с проектом', 'Презентация идеи проекта, возможностей платформы и процесса обучения.', 1, TRUE),
    (25, 11, 'Урок 2. Видеодемонстрация платформы', 'Видеообзор уроков, практических заданий, тестов и AI-наставника.', 2, TRUE)
ON CONFLICT (lesson_id) DO UPDATE SET
    title = EXCLUDED.title, description = EXCLUDED.description,
    is_published = TRUE, updated_at = NOW();

INSERT INTO course_images (course_id, file_id, object_key, content_type, size_bytes, width, height)
VALUES (4, 'c_platform_demo', '4/main.webp', 'image/webp', 116742, 1672, 941)
ON CONFLICT (course_id) DO UPDATE SET
    object_key = EXCLUDED.object_key, content_type = EXCLUDED.content_type,
    size_bytes = EXCLUDED.size_bytes, width = EXCLUDED.width, height = EXCLUDED.height,
    updated_at = NOW();

-- Metadata inspected from the supplied WebP files. Slide order is in Markdown.
INSERT INTO media_files (
    media_key, course_id, object_key, kind, content_type, size_bytes, width, height, original_name
) VALUES
    ('m_4dea8d0fb6ec48a3', 4, '4/media/m_4dea8d0fb6ec48a3.webp', 'image', 'image/webp', 396156, 5333, 3000, 'm_4dea8d0fb6ec48a3.webp'),
    ('m_6f1b227d780a4dd4', 4, '4/media/m_6f1b227d780a4dd4.webp', 'image', 'image/webp', 202112, 5333, 3000, 'm_6f1b227d780a4dd4.webp'),
    ('m_8dc4d47039f549eb', 4, '4/media/m_8dc4d47039f549eb.webp', 'image', 'image/webp', 203910, 5333, 3000, 'm_8dc4d47039f549eb.webp'),
    ('m_19b79c524ab049bf', 4, '4/media/m_19b79c524ab049bf.webp', 'image', 'image/webp', 388168, 5333, 3000, 'm_19b79c524ab049bf.webp'),
    ('m_50feb5160ebb486b', 4, '4/media/m_50feb5160ebb486b.webp', 'image', 'image/webp', 119082, 1920, 1081, 'm_50feb5160ebb486b.webp'),
    ('m_0455f83341ff4745', 4, '4/media/m_0455f83341ff4745.webp', 'image', 'image/webp', 181484, 5333, 3000, 'm_0455f83341ff4745.webp'),
    ('m_794e320f1853432f', 4, '4/media/m_794e320f1853432f.webp', 'image', 'image/webp', 229056, 5333, 3000, 'm_794e320f1853432f.webp'),
    ('m_970e29cf4fb0408d', 4, '4/media/m_970e29cf4fb0408d.webp', 'image', 'image/webp', 181218, 5333, 3000, 'm_970e29cf4fb0408d.webp'),
    ('m_2222cf6fe532495a', 4, '4/media/m_2222cf6fe532495a.webp', 'image', 'image/webp', 376102, 5333, 3000, 'm_2222cf6fe532495a.webp'),
    ('m_3543df34f578444a', 4, '4/media/m_3543df34f578444a.webp', 'image', 'image/webp', 228612, 5333, 3000, 'm_3543df34f578444a.webp')
ON CONFLICT (media_key) DO UPDATE SET
    object_key = EXCLUDED.object_key, kind = EXCLUDED.kind, content_type = EXCLUDED.content_type,
    size_bytes = EXCLUDED.size_bytes, width = EXCLUDED.width, height = EXCLUDED.height,
    original_name = EXCLUDED.original_name, updated_at = NOW()
WHERE media_files.course_id = EXCLUDED.course_id;

INSERT INTO lesson_media (lesson_id, media_id)
SELECT 24, media_id FROM media_files
WHERE course_id = 4 AND kind = 'image' AND media_key IN (
    'm_4dea8d0fb6ec48a3', 'm_6f1b227d780a4dd4', 'm_8dc4d47039f549eb',
    'm_19b79c524ab049bf', 'm_50feb5160ebb486b', 'm_0455f83341ff4745',
    'm_794e320f1853432f', 'm_970e29cf4fb0408d', 'm_2222cf6fe532495a', 'm_3543df34f578444a'
)
ON CONFLICT (lesson_id, media_id) DO NOTHING;

-- Pending upload: size 0 means unknown, not a fabricated file measurement.
-- Verified metadata are NOT overwritten on subsequent seed runs.
INSERT INTO media_files (media_key, course_id, object_key, kind, content_type, size_bytes, original_name)
VALUES ('m_bb0da2e8512e430r', 4, '4/media/m_bb0da2e8512e430r.mp4', 'video', 'video/mp4', 0, 'm_bb0da2e8512e430r.mp4')
ON CONFLICT (media_key) DO NOTHING;

INSERT INTO lesson_media (lesson_id, media_id)
SELECT 25, media_id FROM media_files
WHERE course_id = 4 AND media_key = 'm_bb0da2e8512e430r'
ON CONFLICT (lesson_id, media_id) DO NOTHING;

SELECT setval(pg_get_serial_sequence('courses', 'course_id'),
    GREATEST((SELECT MAX(course_id) FROM courses), nextval(pg_get_serial_sequence('courses', 'course_id'))), TRUE);
SELECT setval(pg_get_serial_sequence('course_modules', 'module_id'),
    GREATEST((SELECT MAX(module_id) FROM course_modules), nextval(pg_get_serial_sequence('course_modules', 'module_id'))), TRUE);
SELECT setval(pg_get_serial_sequence('lessons', 'lesson_id'),
    GREATEST((SELECT MAX(lesson_id) FROM lessons), nextval(pg_get_serial_sequence('lessons', 'lesson_id'))), TRUE);
