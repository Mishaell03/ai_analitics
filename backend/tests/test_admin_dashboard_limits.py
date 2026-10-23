"""Дашборд и список пользователей: ограничение выборки, параллелизма presign и отказоустойчивость MinIO."""

import asyncio
import inspect
from types import SimpleNamespace

from app.api.v1.services import admin as admin_module
from app.api.v1.services.admin import (
    DEFAULT_DASHBOARD_ITEMS,
    MAX_DASHBOARD_ITEMS,
    AdminService,
)
from app.core.minio_url import minio_storage


def test_clamp_count_never_returns_unbounded_limit():
    assert AdminService._clamp_count(None) == DEFAULT_DASHBOARD_ITEMS
    assert AdminService._clamp_count(0) == 1
    assert AdminService._clamp_count(-5) == 1
    assert AdminService._clamp_count(10) == 10
    assert AdminService._clamp_count(10_000) == MAX_DASHBOARD_ITEMS


def test_get_dashboard_defaults_are_bounded():
    signature = inspect.signature(AdminService.get_dashboard)

    assert signature.parameters["users"].default == DEFAULT_DASHBOARD_ITEMS
    assert signature.parameters["top_courses"].default == DEFAULT_DASHBOARD_ITEMS


def test_avatar_presign_concurrency_is_limited_for_dashboard_and_users(monkeypatch):
    state = {"active": 0, "max_active": 0}

    async def fake_avatar_url(img, is_default_img):
        state["active"] += 1
        state["max_active"] = max(state["max_active"], state["active"])

        await asyncio.sleep(0.01)

        state["active"] -= 1

        return f"https://minio/{img}.webp"

    monkeypatch.setattr(admin_module, "get_avatar_url", fake_avatar_url)
    monkeypatch.setattr(admin_module.settings, "minio_presign_concurrency", 3)

    # 1. Проверяем 6-элементные строки дашборда
    rows_dashboard = [
        (user_id, None, None, f"user{user_id}", True, None)
        for user_id in range(10)
    ]

    service = AdminService(db=None)
    urls = asyncio.run(service._presign_avatars(rows_dashboard))

    assert len(urls) == 10
    assert state["max_active"] <= 3

    # 2. Проверяем объекты пользователей из get_users (10 полей)
    state["active"] = 0
    state["max_active"] = 0

    rows_users = [
        SimpleNamespace(
            user_id=i,
            name=f"User {i}",
            email=f"user{i}@example.com",
            phone=None,
            img=f"avatar_{i}",
            is_default_img=False,
            is_admin=False,
            is_blocked=False,
            created_at=None,
            active_sessions=1,
            enrollments=0,
        )
        for i in range(10)
    ]

    urls_users = asyncio.run(service._presign_avatars(rows_users))
    assert len(urls_users) == 10
    assert state["max_active"] <= 3


def test_minio_network_timeout_returns_none_gracefully(monkeypatch):
    """Сетевой сбой или таймаут MinIO не должен ронять запрос с кодом 500."""
    def fake_stat_crash(*args, **kwargs):
        raise TimeoutError("Connection to MinIO timed out")

    monkeypatch.setattr(minio_storage, "get_url", minio_storage.get_url)
    monkeypatch.setattr(admin_module.settings.minio_client, "stat_object", fake_stat_crash)

    # При таймауте stat_object get_url возвращает None, а не бросает исключение
    url = asyncio.run(minio_storage.get_url("avatar.webp", "avatars", check_exists=True))
    assert url is None
