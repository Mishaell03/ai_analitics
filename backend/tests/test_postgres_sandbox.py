"""Opt-in integration checks; only a uniquely named, disposable PostgreSQL is used."""

import os
from pathlib import Path
import secrets
import subprocess
import time
import uuid

import pytest


pytestmark = pytest.mark.skipif(
    os.getenv("POSTGRES_SANDBOX_TESTS") != "1", reason="PostgreSQL Docker tests are opt-in",
)
INIT = Path(__file__).resolve().parents[1] / "infra/postgres/init"
SCRIPT = "/docker-entrypoint-initdb.d/001_create_sandbox_user.sql"


class Postgres:
    def __init__(self):
        self.name = "analytics-postgres-test-" + uuid.uuid4().hex
        self.password = secrets.token_urlsafe(32) + "'quoted"

    def run(self, *args, **kwargs):
        return subprocess.run(args, text=True, capture_output=True, timeout=30, **kwargs)

    def command(self, reader=False, database="analytics_training"):
        return [
            "docker", "exec", "-i", "-e", "PGPASSWORD=" + self.password, self.name,
            "psql", "-X", "-v", "ON_ERROR_STOP=1", "-h", "127.0.0.1", "-U",
            "sandbox_reader" if reader else "postgres", "-d", database, "-At",
        ]

    def sql(self, query, reader=False, database="analytics_training"):
        return self.run(*self.command(reader, database), input=query)

    def ok(self, query, reader=False, database="analytics_training"):
        result = self.sql(query, reader, database)
        assert result.returncode == 0, result.stderr.replace(self.password, "[REDACTED]")
        return result.stdout.strip()

    def apply(self, *environment):
        return self.run(
            "docker", "exec", self.name, *environment, "psql", "-X", "-U", "postgres",
            "-d", "postgres", "-f", SCRIPT,
        )


@pytest.fixture(scope="module")
def pg():
    pg = Postgres()
    try:
        result = pg.run(
            "docker", "create", "--pull=never", "--name", pg.name, "--network", "none",
            "--tmpfs", "/var/lib/postgresql", "-e", "POSTGRES_USER=postgres",
            "-e", "POSTGRES_DB=postgres", "-e", "POSTGRES_PASSWORD=" + pg.password,
            "-e", "SANDBOX_DB_PASSWORD=" + pg.password, "postgres:18.6-trixie",
        )
        assert result.returncode == 0, result.stderr
        # No host bind mount: also works with Fedora SELinux and Docker Desktop.
        result = pg.run("docker", "cp", str(INIT) + "/.", pg.name + ":/docker-entrypoint-initdb.d")
        assert result.returncode == 0, result.stderr
        assert pg.run("docker", "start", pg.name).returncode == 0
        for _ in range(90):
            logs = pg.run("docker", "logs", pg.name)
            if "PostgreSQL init process complete" in logs.stdout and pg.sql("SELECT 1").returncode == 0:
                break
            running = pg.run("docker", "inspect", "-f", "{{.State.Running}}", pg.name)
            assert running.stdout.strip() == "true", (logs.stdout + logs.stderr).replace(pg.password, "[REDACTED]")
            time.sleep(0.5)
        else:
            pytest.fail("Isolated PostgreSQL did not become ready")
        assert pg.password not in logs.stdout + logs.stderr
        assert pg.ok("SELECT count(*) FROM pg_tables WHERE schemaname='public'") == "0"
        pg.ok("CREATE TABLE public.approved_training(id integer); INSERT INTO public.approved_training VALUES(42)")
        yield pg
    finally:
        # This exact random container has no product mounts or published ports.
        pg.run("docker", "rm", "-f", pg.name)


def test_role_settings_and_safe_rerun(pg):
    snapshot = "SELECT datname, datdba, datacl FROM pg_database WHERE datname <> 'analytics_training' ORDER BY datname"
    before = pg.ok(snapshot, database="postgres")
    result = pg.apply()
    assert result.returncode == 0, result.stderr
    assert pg.password not in result.stdout + result.stderr
    assert "public_connect" in result.stdout and "connect_via_set_role" in result.stdout
    assert "pg_catalog.pg_settings" in result.stderr and "set_config" in result.stderr
    assert pg.ok(snapshot, database="postgres") == before
    assert pg.ok("SELECT * FROM public.approved_training", True) == "42"
    assert pg.ok("SELECT rolsuper OR rolcreatedb OR rolcreaterole OR rolinherit OR rolreplication OR rolbypassrls FROM pg_roles WHERE rolname='sandbox_reader'") == "f"
    assert pg.ok("SELECT rolconnlimit FROM pg_roles WHERE rolname='sandbox_reader'") == "5"
    assert pg.ok("SHOW default_transaction_read_only; SHOW statement_timeout; SHOW transaction_timeout; SHOW lock_timeout; SHOW idle_in_transaction_session_timeout", True) == "on\n5s\n10s\n2s\n10s"
    assert pg.ok("SELECT 1", database="core_db") == "1"
    assert pg.ok("SELECT 1", True, "core_db") == "1"  # PUBLIC CONNECT remains.
    for reader, database in [(False, "analytics_training"), (False, "core_db"), (True, "core_db")]:
        assert pg.ok("SHOW default_transaction_read_only; SHOW statement_timeout; SHOW transaction_timeout; SHOW lock_timeout; SHOW idle_in_transaction_session_timeout", reader, database) == "off\n0\n0\n0\n0"


def test_defaults_are_not_a_security_boundary(pg):
    # Changing the session defaults must remain an explicitly documented risk.
    output = pg.ok("SET statement_timeout=0; SET transaction_timeout=0; SET lock_timeout=0; SET default_transaction_read_only=off; SHOW statement_timeout; SHOW transaction_timeout; SHOW lock_timeout; SHOW default_transaction_read_only", True)
    assert output.endswith("0\n0\n0\noff")
    # A fresh connection gets the configured defaults again.
    assert pg.ok("SHOW statement_timeout", True) == "5s"


@pytest.mark.parametrize("query", [
    "INSERT INTO public.approved_training VALUES(1)",
    "UPDATE public.approved_training SET id=1",
    "DELETE FROM public.approved_training",
    "CREATE TABLE public.denied(id integer)",
    "DROP TABLE public.approved_training",
    "CREATE TEMP TABLE denied(id integer)",
])
def test_write_denied_by_privileges_not_just_defaults(pg, query):
    result = pg.sql("SET default_transaction_read_only=off; " + query, True)
    assert result.returncode != 0
    assert "permission denied" in result.stderr or "must be owner" in result.stderr


@pytest.mark.parametrize("environment", [
    ("env", "-u", "SANDBOX_DB_PASSWORD"), ("env", "SANDBOX_DB_PASSWORD="),
])
def test_missing_password(pg, environment):
    result = pg.apply(*environment)
    assert result.returncode != 0 and "must be set and non-empty" in result.stderr


def test_existing_membership_is_not_removed(pg):
    pg.ok("GRANT pg_monitor TO sandbox_reader WITH INHERIT TRUE, SET TRUE")
    try:
        result = pg.apply()
        assert result.returncode != 0 and "existing role memberships" in result.stderr
        assert pg.ok("SELECT pg_has_role('sandbox_reader','pg_monitor','SET')") == "t"
    finally:
        pg.ok("REVOKE pg_monitor FROM sandbox_reader")


@pytest.mark.parametrize("object_sql,grant_sql,expected", [
    ("CREATE TABLE audit_extra.hidden(id integer)", "GRANT UPDATE(id) ON audit_extra.hidden TO PUBLIC", "audit_extra.hidden"),
    ("CREATE SEQUENCE audit_extra.seq", "GRANT USAGE ON audit_extra.seq TO PUBLIC", "audit_extra.seq"),
    ("", "GRANT CREATE ON SCHEMA audit_extra TO PUBLIC", "schema audit_extra"),
])
def test_effective_write_audit_outside_public(pg, object_sql, grant_sql, expected):
    pg.ok("CREATE SCHEMA audit_extra; GRANT USAGE ON SCHEMA audit_extra TO PUBLIC")
    try:
        if object_sql:
            pg.ok(object_sql)
        pg.ok(grant_sql)
        result = pg.apply()
        assert result.returncode != 0 and expected in result.stderr
        # The initializer must not silently revoke the unsafe pre-existing grant.
        if "UPDATE" in grant_sql:
            assert pg.ok("SELECT has_any_column_privilege('sandbox_reader','audit_extra.hidden','UPDATE')") == "t"
    finally:
        pg.ok("DROP SCHEMA audit_extra CASCADE")


def test_function_ownership_and_execute_audit(pg):
    pg.ok("CREATE SCHEMA audit_extra; GRANT USAGE ON SCHEMA audit_extra TO PUBLIC; CREATE TABLE audit_extra.readable(id integer); GRANT SELECT ON audit_extra.readable TO PUBLIC; CREATE FUNCTION audit_extra.elevated() RETURNS integer LANGUAGE sql SECURITY DEFINER AS 'SELECT 1'")
    try:
        result = pg.apply()
        assert result.returncode == 0, result.stderr
        assert "audit_extra.elevated()" in result.stderr and "SECURITY DEFINER=t" in result.stderr
        assert "audit_extra.readable" in result.stderr and "outside approved" in result.stderr
        pg.ok("ALTER FUNCTION audit_extra.elevated() OWNER TO sandbox_reader")
        result = pg.apply()
        assert result.returncode != 0 and "owns training object" in result.stderr
        assert pg.ok("SELECT pg_get_userbyid(proowner) FROM pg_proc WHERE oid='audit_extra.elevated()'::regprocedure") == "sandbox_reader"
    finally:
        pg.ok("DROP SCHEMA audit_extra CASCADE")


def test_statement_and_transaction_timeouts(pg):
    result = pg.sql("SELECT pg_sleep(6)", True)
    assert result.returncode != 0 and "statement timeout" in result.stderr
    # Each statement is shorter than 5s, but their transaction exceeds 10s.
    result = pg.sql("BEGIN; " + "SELECT pg_sleep(3); " * 4, True)
    assert result.returncode != 0 and "transaction timeout" in result.stderr


def test_lock_timeout(pg):
    blocker = subprocess.Popen(pg.command(), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    try:
        blocker.stdin.write("BEGIN; LOCK public.approved_training IN ACCESS EXCLUSIVE MODE; SELECT 'locked';\n")
        blocker.stdin.flush()
        assert blocker.stdout.readline().strip() == "BEGIN"
        assert blocker.stdout.readline().strip() == "LOCK TABLE"
        assert blocker.stdout.readline().strip() == "locked"
        started = time.monotonic()
        result = pg.sql("SELECT * FROM public.approved_training", True)
        assert result.returncode != 0 and "lock timeout" in result.stderr
        assert time.monotonic() - started < 5
    finally:
        blocker.communicate("ROLLBACK;\n", timeout=10)


def test_five_connections_and_sixth_rejected(pg):
    sessions = []
    try:
        for _ in range(5):
            process = subprocess.Popen(pg.command(True), stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            sessions.append(process)
            process.stdin.write("SELECT 1;\n")
            process.stdin.flush()
            assert process.stdout.readline().strip() == "1"
        result = pg.sql("SELECT 1", True)
        assert result.returncode != 0 and "too many connections for role" in result.stderr
        assert pg.ok("SELECT 1", database="core_db") == "1"
    finally:
        for process in sessions:
            process.communicate("\\q\n", timeout=10)
