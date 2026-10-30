-- Catalog order is independent of persistent course IDs and MinIO paths.
ALTER TABLE courses ADD COLUMN sort_order INTEGER NOT NULL DEFAULT 100;
CREATE INDEX ix_courses_sort_order ON courses (sort_order, course_id);
