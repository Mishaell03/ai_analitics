"""ТЕСТЫ КОНТРАКТА, ДОСТУПА И ОГРАНИЧЕНИЙ SANDBOX (БЕЗ БД)."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI, HTTPException
from pydantic import ValidationError

from app.api.v1.routes.sandbox import router
from app.api.v1.schemas.sandbox import RunnerExecutionRequest, SandboxExecuteRequest
from app.api.v1.services.sandbox import SandboxService
from app.core.database import get_db
from app.core.session import get_current_user
from app.services.sandbox.config import MAX_CODE_BYTES, SandboxSettings, get_sandbox_limits
from app.services.sandbox.runner import SandboxBusy, SandboxRunner, create_app


def request_data(**kwargs):
    return SandboxExecuteRequest(
        **dict(course_slug="python", module_id=2, lesson_id=3, exercise_id="py-1", code="print(42)", **kwargs)
    )


@pytest.mark.parametrize("profile", ["", "extreme", "--privileged"])
def test_invalid_profiles(profile):
    with pytest.raises(ValueError):
        get_sandbox_limits(profile)
    with pytest.raises(ValidationError):
        RunnerExecutionRequest(code="print(1)", profile=profile)


def test_students_cannot_supply_limits():
    with pytest.raises(ValidationError):
        request_data(profile="heavy")
    with pytest.raises(ValidationError):
        RunnerExecutionRequest(code="я" * MAX_CODE_BYTES, profile="light")
    limits = get_sandbox_limits("light")
    limits["memory"] = "100g"
    assert get_sandbox_limits("light")["memory"] == "256m"


def test_invalid_unicode_is_validation_error():
    with pytest.raises(ValidationError):
        RunnerExecutionRequest(code="\ud800", profile="light")


@pytest.mark.parametrize("setting,value", [
    ("SANDBOX_CONCURRENCY", "4"), ("SANDBOX_HEAVY_CONCURRENCY", "2"),
    ("SANDBOX_ASSIGNMENT_PROFILES", '{"3:py-1":"invalid"}'),
])
def test_unsafe_configuration_rejected(monkeypatch, setting, value):
    monkeypatch.setenv(setting, value)
    with pytest.raises(ValueError):
        SandboxSettings()


def test_security_arguments():
    args = SandboxRunner(SandboxSettings()).create_args("test", "light")
    for flag, value in {
        "--network": "none", "--user": "65534:65534", "--cap-drop": "ALL",
        "--security-opt": "no-new-privileges:true", "--memory": "256m",
        "--memory-swap": "256m", "--cpus": "0.25", "--pids-limit": "64",
        "--log-driver": "none", "--runtime": "runc",
    }.items():
        assert args[args.index(flag) + 1] == value
    assert "--read-only" in args
    assert "--volume" not in args and "--mount" not in args
    assert "--signal=KILL" in args


def test_runner_authentication_and_body_limit(monkeypatch):
    monkeypatch.setenv("SANDBOX_RUNNER_TOKEN", "t" * 32)
    app = create_app()
    app.state.runner.execute = AsyncMock()

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            denied = await client.post("/execute", json={"code": "pass", "profile": "light"})
            invalid = await client.post("/execute", json={"code": "pass", "profile": "invalid"},
                                        headers={"Authorization": "Bearer " + "t" * 32})
            large = await client.post("/execute", content=b"x" * (MAX_CODE_BYTES * 6 + 4097))
        assert denied.status_code == 401
        assert invalid.status_code == 422
        assert large.status_code == 413
        app.state.runner.execute.assert_not_awaited()
    asyncio.run(scenario())


def test_public_route_requires_authentication():
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.dependency_overrides[get_db] = lambda: None

    async def denied():
        raise HTTPException(401)

    app.dependency_overrides[get_current_user] = denied

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/sandbox/execute", json=request_data().model_dump())
        assert response.status_code == 401
    asyncio.run(scenario())


@pytest.mark.parametrize("enrolled,exists,profile", [
    (False, True, "heavy"), (True, False, "heavy"), (True, True, None), (True, True, "light"),
])
def test_assignment_access_and_trusted_profile(monkeypatch, enrolled, exists, profile):
    from app.api.v1.services import sandbox as service_module

    monkeypatch.setenv("SANDBOX_ASSIGNMENT_PROFILES", json.dumps({"3:py-1": profile} if profile else {}))
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(
        scalar_one_or_none=Mock(return_value=1 if exists else None))))
    service = SandboxService(db)
    service._raise = AsyncMock(side_effect=HTTPException(403))
    monkeypatch.setattr(service_module.StudentExerciseService, "get_exercise", AsyncMock(
        return_value=SimpleNamespace(language="python"),
        side_effect=None if enrolled else HTTPException(403),
    ))
    execute = AsyncMock(return_value="result")
    monkeypatch.setattr(service_module, "execute_code", execute)
    current = SimpleNamespace(user=SimpleNamespace(user_id=7), session=SimpleNamespace(
        language="en", device_id="d", id=1, platform="web"))

    async def scenario():
        if enrolled and exists and profile:
            assert await service.execute(object(), request_data(), current) == "result"
            execute.assert_awaited_once_with(code="print(42)", profile="light")
        else:
            with pytest.raises(HTTPException):
                await service.execute(object(), request_data(), current)
            execute.assert_not_awaited()
    asyncio.run(scenario())


def test_cleanup_after_create_failure():
    runner = SandboxRunner(SandboxSettings())
    runner._docker = AsyncMock(side_effect=RuntimeError("create failed"))
    runner.remove = AsyncMock()
    with pytest.raises(RuntimeError):
        asyncio.run(runner.execute("pass", "light"))
    runner.remove.assert_awaited_once()
    assert runner.active == 0


def test_capacity_is_in_runner_not_api():
    runner = SandboxRunner(SandboxSettings())
    runner.active = 3
    with pytest.raises(SandboxBusy):
        asyncio.run(runner.execute("pass", "light"))
    runner.active = 1
    runner.heavy_active = 1
    with pytest.raises(SandboxBusy):
        asyncio.run(runner.execute("pass", "heavy"))


def test_cleanup_failure_blocks_new_executions():
    runner = SandboxRunner(SandboxSettings())
    runner._docker = AsyncMock(side_effect=RuntimeError("create failed"))
    runner.remove = AsyncMock(side_effect=RuntimeError("daemon unavailable"))
    with pytest.raises(RuntimeError):
        asyncio.run(runner.execute("pass", "light"))
    assert not runner.healthy
    assert len(runner.pending_cleanup) == 1
    assert runner.active == runner.heavy_active == 0


def test_runner_internal_errors_are_not_exposed(monkeypatch):
    monkeypatch.setenv("SANDBOX_RUNNER_TOKEN", "t" * 32)
    app = create_app()
    app.state.runner.execute = AsyncMock(side_effect=RuntimeError("private Docker details"))

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/execute", json={"code": "pass", "profile": "light"},
                                         headers={"Authorization": "Bearer " + "t" * 32})
        assert response.status_code == 503
        assert "private" not in response.text
        assert "Retry-After" not in response.headers
    asyncio.run(scenario())


@pytest.mark.parametrize("busy", [True, False])
def test_transport_distinguishes_busy_and_unavailable(monkeypatch, busy):
    from app.services.sandbox import transport

    monkeypatch.setenv("SANDBOX_RUNNER_TOKEN", "t" * 32)
    client_class = httpx.AsyncClient

    def respond(request):
        assert request.headers["Authorization"] == "Bearer " + "t" * 32
        assert json.loads(request.content)["profile"] == "light"
        return httpx.Response(503, headers={"Retry-After": "1"} if busy else {}, text="private details")

    monkeypatch.setattr(transport.httpx, "AsyncClient", lambda **kwargs: client_class(
        **kwargs, transport=httpx.MockTransport(respond)))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(transport.execute_code("pass", "light"))
    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == ("SANDBOX_BUSY" if busy else "SANDBOX_UNAVAILABLE")
    assert "private" not in str(exc.value.detail)


def test_public_body_limit_before_validation():
    from app.core.exception_handlers import RequestBodyMiddleware
    from app.services.sandbox.config import MAX_REQUEST_BYTES

    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    app.add_middleware(RequestBodyMiddleware)

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.post("/api/v1/sandbox/execute", content=b"x" * (MAX_REQUEST_BYTES + 1))
        assert response.status_code == 413
        assert response.json()["detail"]["code"] == "PAYLOAD_TOO_LARGE"
    asyncio.run(scenario())


def test_transport_has_total_deadline(monkeypatch):
    from app.services.sandbox import transport

    monkeypatch.setenv("SANDBOX_RUNNER_TOKEN", "t" * 32)
    client_class = httpx.AsyncClient
    timeout = asyncio.timeout
    deadlines = []

    def short_deadline(seconds):
        deadlines.append(seconds)
        return timeout(0.01)

    async def slow_response(request):
        await asyncio.sleep(1)
        return httpx.Response(200)

    monkeypatch.setattr(transport.asyncio, "timeout", short_deadline)
    monkeypatch.setattr(transport.httpx, "AsyncClient", lambda **kwargs: client_class(
        **kwargs, transport=httpx.MockTransport(slow_response)))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(transport.execute_code("pass", "light"))
    assert deadlines == [45]
    assert exc.value.status_code == 503
    assert exc.value.detail["code"] == "SANDBOX_UNAVAILABLE"


def test_api_image_has_no_docker_socket():
    from pathlib import Path

    compose = Path("docker-compose.yaml").read_text()
    api = compose.split("  sandbox_api:", 1)[1].split("  postgres:", 1)[0]
    assert "docker.sock" not in api and "volumes:" not in api
    assert 'user: "65534:65534"' in api
    assert "docker.io" not in Path("app/Dockerfile").read_text()
    runner_image = Path("infra/sandbox/runner.Dockerfile").read_text()
    assert "--no-install-recommends docker-cli" in runner_image
    assert "--no-install-recommends docker.io" not in runner_image
