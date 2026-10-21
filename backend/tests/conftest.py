"""ОБЩИЕ НАСТРОЙКИ ТЕСТОВ"""

import asyncio
import socket

import pytest

from app.core.config import settings

# один event loop на весь запуск тестов: подключения asyncpg привязаны
# к loop, в котором были созданы, и переиспользовать их в другом
# loop нельзя
LOOP = asyncio.new_event_loop()


@pytest.fixture(scope="session", autouse=True)
def _close_loop():
    """ЗАКРЫВАЕТ EVENT LOOP ПОСЛЕ ЗАПУСКА ТЕСТОВ"""

    yield

    LOOP.close()


def infrastructure_available() -> bool:
    """ПОДНЯТЫ ЛИ БАЗА И ХРАНИЛИЩЕ

    Проверяем порты, а не подключаемся к базе: подключение создало
    бы соединение в одноразовом loop, и пул потом отдал бы его
    в другом.
    """

    minio_host, _, minio_port = settings.minio_endpoint.partition(":")

    for host, port in (
        (settings.db_host, settings.db_port),
        (minio_host, int(minio_port or 9000)),
    ):
        try:
            with socket.create_connection((host, port), timeout=2):
                pass

        except OSError:
            return False

    return True
