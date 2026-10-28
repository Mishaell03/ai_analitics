"""Настройки только backend. Адрес Google фиксирован, прокси обязателен."""

import os
import re
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlsplit

from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[3]
CONTEXT_PATH = ROOT / "infra/llm/context.md"


class LLMSettings:
    def __init__(self):
        defaults = {**dotenv_values(ROOT / ".env"), **dotenv_values(ROOT / "app/.env")}

        def setting(name, default=""):
            return os.environ.get(name, defaults.get(name) or default)

        self.api_key = setting("GEMINI_API_KEY")
        self.proxy = setting("GEMINI_PROXY_URL", "http://127.0.0.1:10810")
        model_list = setting("GEMINI_MODELS", setting("GEMINI_MODEL", "gemini-3.5-flash-lite"))
        self.models = list(dict.fromkeys(item.strip() for item in model_list.split(",") if item.strip()))
        self.model = self.models[0] if self.models else ""
        self.daily_limit = int(setting("GEMINI_USER_DAILY_LIMIT", "50"))
        self.minute_limit = int(setting("GEMINI_USER_MINUTE_LIMIT", "5"))
        if not 1 <= len(self.models) <= 5 or any(
            not re.fullmatch(r"gemini-[a-zA-Z0-9.-]{1,80}", model) for model in self.models
        ):
            raise ValueError("GEMINI_MODELS must contain 1 to 5 valid models")
        proxy = urlsplit(self.proxy)
        if proxy.scheme not in {"http", "https"} or not proxy.hostname or not proxy.port:
            raise ValueError("GEMINI_PROXY_URL must specify an HTTP proxy and port")
        if proxy.path not in {"", "/"} or proxy.query or proxy.fragment:
            raise ValueError("Invalid Gemini proxy URL")
        if not 1 <= self.daily_limit <= 500 or not 1 <= self.minute_limit <= 20:
            raise ValueError("Invalid Gemini request limits")


@lru_cache(maxsize=1)
def system_context() -> str:
    context = CONTEXT_PATH.read_text(encoding="utf-8").strip()
    if not context or len(context) > 24000:
        raise ValueError("LLM context is empty or too large")
    return context
