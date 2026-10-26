import json
import os
from typing import Final

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
        self.image = os.getenv("SANDBOX_IMAGE", "analytics-sandbox:1.0")
        self.runtime = os.getenv("SANDBOX_RUNTIME", "runc")
        self.endpoint = os.getenv("SANDBOX_RUNNER_ENDPOINT", "http://127.0.0.1:8090")
        self.token = os.getenv("SANDBOX_RUNNER_TOKEN", "")
        self.concurrency = int(os.getenv("SANDBOX_CONCURRENCY", "3"))
        self.heavy_concurrency = int(os.getenv("SANDBOX_HEAVY_CONCURRENCY", "1"))
        self.lock_file = os.getenv("SANDBOX_LOCK_FILE", ".sandbox-runner.lock")
        if not 1 <= self.concurrency <= 3 or self.heavy_concurrency != 1:
            raise ValueError("Sandbox concurrency may only reduce the safety limits")
        self.assignment_profiles = json.loads(os.getenv("SANDBOX_ASSIGNMENT_PROFILES", "{}"))
        if not isinstance(self.assignment_profiles, dict) or any(
                not isinstance(key, str) or not isinstance(profile, str) or profile not in PROFILES
                for key, profile in self.assignment_profiles.items()
        ):
            raise ValueError("Invalid sandbox assignment profiles")


def get_sandbox_limits(profile: str) -> dict:
    if profile not in PROFILES:
        raise ValueError("Unknown sandbox profile")
    return PROFILES[profile].copy()
