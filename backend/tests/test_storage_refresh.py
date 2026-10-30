"""Обновление MinIO без Docker-операций и удаления настоящих данных."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest


BACKEND = Path(__file__).resolve().parents[1]
SCRIPT = BACKEND / "infra/minio/refresh.sh"


@pytest.fixture
def commands(tmp_path):
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "commands.jsonl"
    stub = f"#!{sys.executable}\n" + """
import json
import os
from pathlib import Path
import sys

args = sys.argv[1:]
name = Path(sys.argv[0]).name
with open(os.environ["COMMAND_LOG"], "a") as stream:
    stream.write(json.dumps([name, *args]) + "\\n")
if name == "docker" and args[:2] == ["compose", "ps"]:
    print(os.environ.get("FAKE_CONTAINER", "running-minio"))
if os.environ.get("FAIL_COMMAND") == (args[0] if args else ""):
    sys.exit(7)
"""
    for name in ("mc", "docker"):
        path = bin_dir / name
        path.write_text(stub)
        path.chmod(0o755)
    seeds = tmp_path / "seeds"
    for bucket in ("default-avatars", "course-content"):
        (seeds / bucket).mkdir(parents=True)
        (seeds / bucket / "seed.txt").write_text("seed")
    env = {
        **os.environ,
        "PATH": f"{bin_dir}:{os.environ['PATH']}",
        "COMMAND_LOG": str(log),
        "MINIO_ROOT_USER": "test-user",
        "MINIO_ROOT_PASSWORD": "test-password",
        "MINIO_SEEDS_DIR": str(seeds),
    }
    return env, log, seeds


def read_commands(log):
    return [json.loads(line) for line in log.read_text().splitlines()] if log.exists() else []


def test_refresh_clears_only_project_buckets_before_seeding(commands):
    env, log, seeds = commands
    result = subprocess.run(["sh", str(SCRIPT)], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    calls = read_commands(log)
    assert calls[0] == ["mc", "alias", "set", "local", "http://127.0.0.1:9000", "test-user", "test-password"]
    assert calls[1:7] == [
        call
        for bucket in ("default-avatars", "avatars", "course-content")
        for call in (
            ["mc", "mb", "--ignore-existing", f"local/{bucket}"],
            ["mc", "rm", "--recursive", "--force", "--versions", f"local/{bucket}"],
        )
    ]
    assert calls[7:] == [
        ["mc", "cp", "--recursive", f"{seeds}/default-avatars/", "local/default-avatars"],
        ["mc", "cp", "--recursive", f"{seeds}/course-content/", "local/course-content"],
    ]


@pytest.mark.parametrize("command", ["alias", "mb", "rm", "cp"])
def test_refresh_stops_on_first_error(commands, command):
    env, log, _ = commands
    result = subprocess.run(["sh", str(SCRIPT)], env={**env, "FAIL_COMMAND": command}, capture_output=True)
    assert result.returncode == 7
    assert read_commands(log)[-1][1] == command


def test_missing_seeds_prevent_any_minio_changes(commands):
    env, log, seeds = commands
    result = subprocess.run(
        ["sh", str(SCRIPT)], env={**env, "MINIO_SEEDS_DIR": str(seeds / "missing")}, capture_output=True,
    )
    assert result.returncode != 0
    assert read_commands(log) == []


def run_make(env):
    return subprocess.run(
        ["make", "--no-print-directory", "storage-refresh", "MINIO_ROOT_USER=test-user", "MINIO_ROOT_PASSWORD=test-password"],
        cwd=BACKEND, env=env, capture_output=True, text=True,
    )


def test_make_reuses_running_minio_network_without_compose_run(commands):
    env, log, _ = commands
    result = run_make(env)
    assert result.returncode == 0, result.stderr
    calls = read_commands(log)
    assert calls[0] == ["docker", "compose", "ps", "--status", "running", "-q", "minio"]
    assert len(calls) == 2
    assert calls[1][:5] == ["docker", "run", "--rm", "--network", "container:running-minio"]
    assert "MINIO_ROOT_PASSWORD" in calls[1]
    assert "test-password" not in calls[1]
    assert calls[1][-1] == "/refresh.sh"
    assert "MinIO refresh completed." in result.stdout


def test_make_requires_running_minio(commands):
    env, log, _ = commands
    result = run_make({**env, "FAKE_CONTAINER": ""})
    assert result.returncode != 0
    assert len(read_commands(log)) == 1
    assert "MinIO is not running" in result.stderr
    assert "MinIO refresh completed." not in result.stdout


def test_make_does_not_report_success_when_refresh_fails(commands):
    env, _, _ = commands
    result = run_make({**env, "FAIL_COMMAND": "run"})
    assert result.returncode != 0
    assert "MinIO refresh completed." not in result.stdout
