"""Backend-only DeepSeek settings: one model and a fixed direct HTTPS endpoint."""

import os
import re
from functools import lru_cache
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
CONTEXT_PATH = ROOT / "infra/llm/mentor.md"
BRIEF_CONTEXT_PATH = ROOT / "infra/llm/brief_context.md"


class LLMSettings:
    def __init__(self):
        defaults = {**dotenv_values(ROOT / ".env"), **dotenv_values(ROOT / "app/.env")}

        def setting(name, default=""):
            return os.environ.get(name, defaults.get(name, default)) or ""

        def integer(name, default, minimum, maximum):
            try:
                value = int(setting(name, str(default)))
            except (ValueError, TypeError):
                raise ValueError(f"{name} must be an integer") from None
            if not minimum <= value <= maximum:
                raise ValueError(f"{name} is outside the allowed range")
            return value

        self.api_key = setting("DEEPSEEK_API_KEY").strip()
        self.model = setting("MODEL", "deepseek-flash").strip()
        if not re.fullmatch(r"deepseek-[a-z0-9-]{1,64}", self.model):
            raise ValueError("MODEL must contain exactly one DeepSeek model name")
        self.thinking = setting("THINKING", "disabled").strip()
        if self.thinking not in {"disabled", "enabled"}:
            raise ValueError("THINKING must be disabled or enabled")
        # Prevent malformed headers without logging the secret itself.
        if any(char.isspace() or ord(char) < 32 or ord(char) > 126 for char in self.api_key):
            raise ValueError("DEEPSEEK_API_KEY contains invalid characters")
        self.daily_limit = integer("DEEPSEEK_USER_DAILY_LIMIT", 50, 1, 500)
        self.minute_limit = integer("DEEPSEEK_USER_MINUTE_LIMIT", 5, 1, 20)
        self.project_daily_limit = integer("DEEPSEEK_PROJECT_DAILY_LIMIT", 200, 1, 10000)
        self.project_minute_limit = integer("DEEPSEEK_PROJECT_MINUTE_LIMIT", 10, 1, 100)
        self.max_input_bytes = integer("DEEPSEEK_MAX_INPUT_BYTES", 18000, 8000, 64000)
        self.max_output_tokens = integer("MAX_TOKENS", 1024, 512, 4096)


@lru_cache(maxsize=1)
def system_context() -> str:
    context = CONTEXT_PATH.read_text(encoding="utf-8").strip()
    if not context or len(context) > 6000:
        raise ValueError("LLM context is empty or too large")
    return context


@lru_cache(maxsize=1)
def brief_context() -> str:
    context = BRIEF_CONTEXT_PATH.read_text(encoding="utf-8").strip()
    if not context or len(context) > 1000:
        raise ValueError("Brief AI context is empty or too large")
    return context
