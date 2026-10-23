"""ПРОСТОЙ RATE LIMIT ДЛЯ АУТЕНТИФИКАЦИИ

Ограничение частоты запросов выполняется в памяти текущего рабочего процесса (in-memory).
Это легковесная защита от перебора паролей и спам-регистрации без необходимости
подключения внешней инфраструктуры (Redis).

Ограничения при работе в кластере / с несколькими воркерами:
- При запуске нескольких воркеров (Uvicorn workers) или нескольких реплик в контейнерах
  каждый процесс ведёт собственный независимый счётчик.
- Эффективный лимит для клиента распределяется балансировщиком нагрузки и составляет
  до (limit * N_workers) запросов за окно при равномерном распределении.
- При перезапуске процесса счётчики сбрасываются.
- Если в будущем требования к строгости лимитов возрастут, класс может быть заменён
  на распределённый Redis Token Bucket / Sliding Window без изменения роутов.
"""

import time
from threading import Lock

from fastapi import HTTPException, Request

from app.core.clients_ip import get_client_ip
from app.core.config import settings


class FixedWindowLimiter:
    """Счётчик запросов в фиксированном окне с защитой от блокировок и утечек памяти."""

    def __init__(self, limit: int, window_seconds: int, max_keys: int = 10_000):
        self.limit = max(1, int(limit))
        self.window_seconds = max(1, int(window_seconds))
        self.max_keys = max(100, int(max_keys))
        self._hits: dict[str, tuple[float, int]] = {}
        self._last_prune: float = 0.0
        self._lock = Lock()

    def allow(self, key: str) -> tuple[bool, int]:
        """(разрешено, через сколько секунд повторить)."""

        now = time.monotonic()

        with self._lock:
            window_start, count = self._hits.get(key, (now, 0))

            if now - window_start >= self.window_seconds:
                window_start, count = now, 0

            if count >= self.limit:
                retry_after = max(
                    1,
                    int(self.window_seconds - (now - window_start)),
                )

                return False, retry_after

            self._hits[key] = (window_start, count + 1)

            # Очистка запускается не чаще одного раза в 5 секунд при превышении max_keys
            if (
                len(self._hits) > self.max_keys
                and (now - self._last_prune) >= min(float(self.window_seconds), 5.0)
            ):
                self._prune(now)

            return True, 0

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()
            self._last_prune = 0.0

    def _prune(self, now: float) -> None:
        self._last_prune = now

        expired = [
            key
            for key, (window_start, _) in self._hits.items()
            if now - window_start >= self.window_seconds
        ]

        for key in expired:
            self._hits.pop(key, None)

        # Если после очистки истёкших записей размер словаря всё ещё превышает удвоенный max_keys
        # (например, при активной распределённой атаке), отсекаем старейшие записи для защиты памяти
        if len(self._hits) > self.max_keys * 2:
            sorted_keys = sorted(self._hits.keys(), key=lambda k: self._hits[k][0])
            for k in sorted_keys[: len(sorted_keys) // 2]:
                self._hits.pop(k, None)


login_limiter = FixedWindowLimiter(
    limit=settings.auth_login_rate_limit,
    window_seconds=settings.auth_rate_limit_window_seconds,
)

register_limiter = FixedWindowLimiter(
    limit=settings.auth_register_rate_limit,
    window_seconds=settings.auth_rate_limit_window_seconds,
)


def reset_auth_rate_limits() -> None:
    """Сброс счётчиков (используется в тестах)."""

    login_limiter.reset()
    register_limiter.reset()


def _rate_limit_key(request: Request) -> str:
    try:
        ip = get_client_ip(request)
        if ip:
            return ip
    except Exception:
        pass

    # Безопасный fallback на сокетный хост клиента
    if getattr(request, "client", None) and getattr(request.client, "host", None):
        return request.client.host

    return "unknown"


def _raise_rate_limited(retry_after: int) -> None:
    raise HTTPException(
        status_code=429,
        detail={
            "code": "TOO_MANY_REQUESTS",
            "message": "Too many requests, try again later",
        },
        headers={"Retry-After": str(retry_after)},
    )


async def login_rate_limit(request: Request) -> None:
    if not settings.auth_rate_limit_enabled:
        return

    allowed, retry_after = login_limiter.allow(_rate_limit_key(request))

    if not allowed:
        _raise_rate_limited(retry_after)


async def register_rate_limit(request: Request) -> None:
    if not settings.auth_rate_limit_enabled:
        return

    allowed, retry_after = register_limiter.allow(_rate_limit_key(request))

    if not allowed:
        _raise_rate_limited(retry_after)
