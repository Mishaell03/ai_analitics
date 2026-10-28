import json
import os
from pathlib import Path
from typing import Final

from dotenv import dotenv_values

PROFILES: Final = {
    "light": {
        "cpu": 0.25,
        "memory": "256m",
        "timeout": 5,
    },
    "standard": {
        "cpu": 0.5,
        "memory": "768m",
        "timeout": 15,
    },
    "heavy": {
        "cpu": 1.0,
        "memory": "1536m",
        "timeout": 30,
    },
}

MAX_CODE_BYTES: Final = 64 * 1024
MAX_OUTPUT_BYTES: Final = 64 * 1024
# JSON может кодировать один символ как шесть байт (\uXXXX).
MAX_REQUEST_BYTES: Final = MAX_CODE_BYTES * 6 + 4096
MANAGED_LABEL: Final = "analytics.sandbox=1"


class SandboxSettings:
    """Не загружает настройки БД/MinIO: runner не должен получать их секреты."""

    def __init__(self):
        # Compose передаёт окружение напрямую; host API и runner используют
        # те же sandbox-настройки из backend/.env, не импортируя прикладные секреты.
        defaults = dotenv_values(Path(__file__).resolve().parents[3] / ".env")
        def setting(name, default=""):
            return os.environ.get(name, defaults.get(name) or default)

        self.image = setting("SANDBOX_IMAGE", "analytics-sandbox:1.0")
        self.runtime = setting("SANDBOX_RUNTIME", "runc")
        self.endpoint = setting("SANDBOX_RUNNER_ENDPOINT", "http://127.0.0.1:8090")
        self.token = setting("SANDBOX_RUNNER_TOKEN")
        self.sql_host = setting("SANDBOX_DB_HOST", "127.0.0.1")
        self.sql_port = int(setting("SANDBOX_DB_PORT", "5432"))
        self.sql_password = setting("SANDBOX_DB_PASSWORD")
        self.concurrency = int(setting("SANDBOX_CONCURRENCY", "3"))
        self.heavy_concurrency = int(setting("SANDBOX_HEAVY_CONCURRENCY", "1"))
        self.lock_file = setting("SANDBOX_LOCK_FILE", ".sandbox-runner.lock")
        if not 1 <= self.concurrency <= 3 or self.heavy_concurrency != 1:
            raise ValueError("Sandbox concurrency may only reduce the safety limits")
        self.assignment_profiles = json.loads(setting("SANDBOX_ASSIGNMENT_PROFILES", "{}"))
        if not isinstance(self.assignment_profiles, dict) or any(
                not isinstance(key, str) or not isinstance(profile, str) or profile not in PROFILES
                for key, profile in self.assignment_profiles.items()
        ):
            raise ValueError("Invalid sandbox assignment profiles")


def get_sandbox_limits(profile: str) -> dict:
    if profile not in PROFILES:
        raise ValueError("Unknown sandbox profile")
    return PROFILES[profile].copy()
