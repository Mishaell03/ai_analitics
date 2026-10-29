"""Flyway должен читать dollar-quoted JSON буквально, без ${...} placeholders."""

import json
import os
from pathlib import Path
import subprocess
import sys

import pytest

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("target", ["seed", "ai-migrate", "logs-migrate"])
def test_seed_commands_disable_placeholder_replacement_without_running_docker(tmp_path, target):
    (tmp_path / "Makefile").write_text((ROOT / "Makefile").read_text())
    (tmp_path / ".env").write_text(
        "DATABASES=analytics_training,core_db\nPOSTGRES_USER=test\nPOSTGRES_PASSWORD=test\nDB_HOST=127.0.0.1\nDB_PORT=5432\n"
    )
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    log = tmp_path / "docker.jsonl"
    docker = bin_dir / "docker"
    docker.write_text(f"#!{sys.executable}\n" + """
import json, os, sys
with open(os.environ["COMMAND_LOG"], "a") as stream:
    stream.write(json.dumps(sys.argv[1:]) + "\\n")
""")
    docker.chmod(0o755)
    result = subprocess.run(["make", "--no-print-directory", target], cwd=tmp_path,
        env={**os.environ, "PATH": f"{bin_dir}:{os.environ['PATH']}", "COMMAND_LOG": str(log)},
        capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    calls = [json.loads(line) for line in log.read_text().splitlines()]
    assert len(calls) == (2 if target == "seed" else 1)
    assert all("-placeholderReplacement=false" in call and call[-1] == "migrate" for call in calls)
