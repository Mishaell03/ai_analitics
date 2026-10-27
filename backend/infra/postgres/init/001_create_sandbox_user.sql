\set ON_ERROR_STOP on
\unset sandbox_password
\getenv sandbox_password SANDBOX_DB_PASSWORD

-- Fail before creating anything if the password is missing or empty.
\if :{?sandbox_password}
SELECT length(:'sandbox_password') > 0 AS has_password \gset
\else
\set has_password false
\endif
\if :has_password
\else
DO $$
BEGIN
    RAISE EXCEPTION 'SANDBOX_DB_PASSWORD must be set and non-empty';
END
$$;
\endif

-- Do not repurpose an administrator or silently remove existing memberships.
-- NOINHERIT alone does not prevent SET ROLE, or override existing membership
-- INHERIT options on PostgreSQL 18. Existing memberships require manual review.
DO $$
BEGIN
    IF current_user = 'sandbox_reader' THEN
        RAISE EXCEPTION 'Run sandbox initialization as the PostgreSQL administrator';
    END IF;
    IF EXISTS (
        SELECT FROM pg_auth_members m
        JOIN pg_roles r ON r.oid = m.member
        WHERE r.rolname = 'sandbox_reader'
    ) THEN
        RAISE EXCEPTION 'sandbox_reader has existing role memberships; review them manually before initialization';
    END IF;
    IF EXISTS (
        SELECT FROM pg_database d
        JOIN pg_roles r ON r.oid = d.datdba
        WHERE r.rolname = 'sandbox_reader'
    ) THEN
        RAISE EXCEPTION 'sandbox_reader owns a database; review ownership manually before initialization';
    END IF;
END
$$;

SELECT 'CREATE ROLE sandbox_reader'
WHERE NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'sandbox_reader') \gexec

SELECT format(
    'ALTER ROLE sandbox_reader LOGIN NOSUPERUSER NOCREATEDB NOCREATEROLE NOINHERIT NOREPLICATION NOBYPASSRLS CONNECTION LIMIT 5 PASSWORD %L',
    :'sandbox_password'
) \gexec
\unset sandbox_password

SELECT 'CREATE DATABASE analytics_training'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'analytics_training') \gexec

-- Audit only: never change application database ACLs. CONNECT from PUBLIC
-- cannot be denied with a role-specific REVOKE. This is not full isolation.
\echo 'Application database CONNECT audit (catalog privileges, not pg_hba.conf):'
SELECT d.datname,
       EXISTS (
           SELECT FROM aclexplode(COALESCE(d.datacl, acldefault('d', d.datdba))) a
           WHERE a.grantee = 0 AND a.privilege_type = 'CONNECT'
       ) AS public_connect,
       has_database_privilege('sandbox_reader', d.oid, 'CONNECT') AS effective_connect,
       EXISTS (
           SELECT FROM pg_roles r
           WHERE r.rolname <> 'sandbox_reader'
             AND pg_has_role('sandbox_reader', r.oid, 'SET')
             AND has_database_privilege(r.oid, d.oid, 'CONNECT')
       ) AS connect_via_set_role
FROM pg_database d
WHERE d.datallowconn AND d.datname <> 'analytics_training'
ORDER BY d.datname;

REVOKE ALL ON DATABASE analytics_training FROM PUBLIC, sandbox_reader;
GRANT CONNECT ON DATABASE analytics_training TO sandbox_reader;

\connect analytics_training

-- Ownership carries implicit DDL rights that REVOKE cannot remove.
DO $$
DECLARE
    owned_object text;
BEGIN
    SELECT pg_describe_object(d.classid, d.objid, d.objsubid)
    INTO owned_object
    FROM pg_shdepend d JOIN pg_roles r ON r.oid = d.refobjid
    WHERE d.refclassid = 'pg_authid'::regclass AND r.rolname = 'sandbox_reader'
      AND d.deptype = 'o'
      AND d.dbid = (SELECT oid FROM pg_database WHERE datname = current_database())
    LIMIT 1;
    IF owned_object IS NOT NULL THEN
        RAISE EXCEPTION 'sandbox_reader owns training object: %. Review ownership manually', owned_object;
    END IF;
END
$$;

REVOKE ALL ON SCHEMA public FROM PUBLIC, sandbox_reader;
GRANT USAGE ON SCHEMA public TO sandbox_reader;
REVOKE ALL ON ALL TABLES IN SCHEMA public FROM sandbox_reader;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA public FROM sandbox_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO sandbox_reader;

-- Applies to tables created by the administrator running this script.
ALTER DEFAULT PRIVILEGES IN SCHEMA public
    GRANT SELECT ON TABLES TO sandbox_reader;

ALTER ROLE sandbox_reader IN DATABASE analytics_training
    SET default_transaction_read_only = on;

ALTER ROLE sandbox_reader IN DATABASE analytics_training
    SET statement_timeout = '5s';

ALTER ROLE sandbox_reader IN DATABASE analytics_training
    SET transaction_timeout = '10s';

ALTER ROLE sandbox_reader IN DATABASE analytics_training
    SET lock_timeout = '2s';

-- PostgreSQL ignores the idle timeout when transaction_timeout is <= it.
-- Keep both defaults: the total transaction lifetime is still capped at 10s.
ALTER ROLE sandbox_reader IN DATABASE analytics_training
    SET idle_in_transaction_session_timeout = '10s';

-- Existing PUBLIC grants can still confer write rights. Refuse an unsafe
-- configuration rather than silently changing permissions of other roles.
DO $$
DECLARE
    item record;
BEGIN
    FOR item IN
        SELECT n.nspname, c.relname
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE c.relkind IN ('r', 'p', 'v', 'm', 'f')
          AND (
              has_table_privilege('sandbox_reader', c.oid, 'INSERT,UPDATE,DELETE,TRUNCATE,REFERENCES,TRIGGER,MAINTAIN')
              OR has_any_column_privilege('sandbox_reader', c.oid, 'INSERT,UPDATE,REFERENCES')
          )
    LOOP
        IF item.nspname = 'pg_catalog' AND item.relname = 'pg_settings' THEN
            -- PostgreSQL's standard PUBLIC UPDATE route changes session GUCs,
            -- not training rows. Report it without breaking a clean cluster.
            RAISE WARNING 'sandbox_reader can UPDATE pg_catalog.pg_settings (session parameters); SQL Runner must prohibit this route as well as SET/set_config';
        ELSE
            RAISE EXCEPTION 'sandbox_reader has effective table/column write privileges on %.%; review grants manually', item.nspname, item.relname;
        END IF;
    END LOOP;

    FOR item IN
        SELECT n.nspname, c.relname
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE CASE WHEN c.relkind = 'S'
              THEN has_sequence_privilege('sandbox_reader', c.oid, 'USAGE,UPDATE')
              ELSE false END
    LOOP
        RAISE EXCEPTION 'sandbox_reader has effective sequence write privileges on %.%; review grants manually', item.nspname, item.relname;
    END LOOP;

    FOR item IN
        SELECT n.nspname FROM pg_namespace n
        WHERE has_schema_privilege('sandbox_reader', n.oid, 'CREATE')
    LOOP
        RAISE EXCEPTION 'sandbox_reader can CREATE in schema %; review grants manually', item.nspname;
    END LOOP;

    -- Report unexpected readable user relations without revoking existing ACLs.
    FOR item IN
        SELECT n.nspname, c.relname
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname <> 'public' AND n.nspname <> 'information_schema'
          AND n.nspname !~ '^pg_'
          AND has_schema_privilege('sandbox_reader', n.oid, 'USAGE')
          AND CASE WHEN c.relkind = 'S'
              THEN has_sequence_privilege('sandbox_reader', c.oid, 'SELECT')
              WHEN c.relkind IN ('r', 'p', 'v', 'm', 'f')
              THEN has_any_column_privilege('sandbox_reader', c.oid, 'SELECT')
              ELSE false END
    LOOP
        RAISE WARNING 'sandbox_reader can read outside approved public schema: %.%; review grants manually', item.nspname, item.relname;
    END LOOP;

    -- EXECUTE is granted to PUBLIC by default. Never execute routine bodies
    -- during this audit, and never revoke shared routine ACLs automatically.
    FOR item IN
        SELECT p.oid::regprocedure AS routine, p.prosecdef,
               pg_get_userbyid(p.proowner) AS owner
        FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
        WHERE has_schema_privilege('sandbox_reader', n.oid, 'USAGE')
          AND has_function_privilege('sandbox_reader', p.oid, 'EXECUTE')
          AND (
              p.prosecdef
              OR (n.nspname <> 'information_schema' AND n.nspname !~ '^pg_')
              OR (n.nspname = 'pg_catalog' AND (
                  p.proname ~ '^(pg_(read|write|ls|stat_file|terminate|cancel|reload|rotate|log_backend|advisory)|lo_(import|export))'
                  OR p.proname IN ('set_config', 'pg_notify')
              ))
          )
    LOOP
        RAISE WARNING 'sandbox_reader has EXECUTE on % (SECURITY DEFINER=%, owner=%); review side effects/privilege escalation before enabling SQL Runner', item.routine, item.prosecdef, item.owner;
    END LOOP;
END
$$;
