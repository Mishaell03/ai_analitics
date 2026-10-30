-- Images referenced by course-content/1/4/11.md and 1/4/12.md.
INSERT INTO media_files (
    media_key, course_id, object_key, kind, content_type, size_bytes,
    width, height, original_name
) VALUES
    ('m_72e62512f7eb67e3', 1, '1/media/m_72e62512f7eb67e3.png',
     'image', 'image/png', 351009, 1672, 941, 'm_72e62512f7eb67e3.png'),
    ('m_45e57512f7eb46e0', 1, '1/media/m_45e57512f7eb46e0.png',
     'image', 'image/png', 261676, 1672, 941, 'm_45e57512f7eb46e0.png')
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
SELECT seed.lesson_id, media.media_id
FROM (VALUES
    (11, 'm_72e62512f7eb67e3'),
    (12, 'm_45e57512f7eb46e0')
) AS seed(lesson_id, media_key)
JOIN media_files media ON media.media_key = seed.media_key AND media.course_id = 1
ON CONFLICT (lesson_id, media_id) DO NOTHING;
