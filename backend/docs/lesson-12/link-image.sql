-- Только ручной запуск владельцем после проверки файла и metadata.
-- psql ... -v lesson_id=<ФАКТИЧЕСКИЙ_ID_SQL_УРОКА> -f docs/lesson-12/link-image.sql
-- Не создаёт изображение, урок или схему; существующие записи не перезаписывает.
\set ON_ERROR_STOP on
\if :{?lesson_id}
\else
\echo 'Нужен фактический lesson_id. ID 12 занят другим уроком: не подставляйте его вслепую.'
\quit 3
\endif

BEGIN;
SELECT EXISTS (
    SELECT 1 FROM lessons l
    JOIN course_modules cm USING (module_id) JOIN courses c USING (course_id)
    WHERE l.lesson_id=:'lesson_id'::integer
      AND c.slug='ai-development-beginner' AND cm.position=4 AND l.position=2
) AS correct_lesson \gset
\if :correct_lesson
\else
ROLLBACK;
\echo 'Целевой урок не соответствует модулю 4, позиции 2 начального курса.'
\quit 3
\endif

SELECT EXISTS (
    SELECT 1 FROM media_files m JOIN courses c USING (course_id)
    WHERE m.media_key='m_45e57512f7eb46e0' AND m.kind='image'
      AND c.slug='ai-development-beginner'
) AS image_registered \gset
\if :image_registered
\else
ROLLBACK;
\echo 'Нет metadata существующего изображения m_45e57512f7eb46e0. Сначала проверьте и зарегистрируйте реальный файл.'
\quit 3
\endif

INSERT INTO lesson_media (lesson_id, media_id)
SELECT :'lesson_id'::integer, media_id FROM media_files
WHERE media_key='m_45e57512f7eb46e0'
ON CONFLICT (lesson_id, media_id) DO NOTHING;

SELECT lm.lesson_id, m.media_id, m.media_key, m.object_key
FROM lesson_media lm JOIN media_files m USING (media_id)
WHERE lm.lesson_id=:'lesson_id'::integer AND m.media_key='m_45e57512f7eb46e0';
COMMIT;
