-- Выполнять владельцем учебных таблиц в analytics_training после пересоздания public.
DO $$
BEGIN
    IF current_database() <> 'analytics_training' THEN
        RAISE EXCEPTION 'Run this script only in analytics_training';
    END IF;
END
$$;

GRANT USAGE ON SCHEMA public TO sandbox_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sandbox_reader;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO sandbox_reader;
