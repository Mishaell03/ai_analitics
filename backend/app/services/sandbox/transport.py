"""Ограниченный внутренний HTTP-интерфейс, без Docker в процессе API."""

import asyncio
import json

import httpx
from fastapi import HTTPException

from app.api.v1.schemas.sandbox import ExecutionResult
from app.services.sandbox.config import MAX_OUTPUT_BYTES, MAX_REQUEST_BYTES, SandboxSettings, get_sandbox_limits


class SandboxBodyLimitMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        body = bytearray()
        while True:
            message = await receive()
            if message["type"] == "http.disconnect":
                return
            chunk = message.get("body", b"")
            if len(body) + len(chunk) > MAX_REQUEST_BYTES:
                payload = b'{"detail":{"code":"PAYLOAD_TOO_LARGE","message":"Request too large"}}'
                await send({"type": "http.response.start", "status": 413,
                            "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": payload})
                return
            body.extend(chunk)
            if not message.get("more_body", False):
                break

        async def buffered_receive():
            nonlocal body
            if body is None:
                return await receive()
            payload = bytes(body)
            body = None
            return {"type": "http.request", "body": payload, "more_body": False}

        await self.app(scope, buffered_receive, send)


async def execute_code(code: str, profile: str, language: str = "python") -> ExecutionResult:
    config = SandboxSettings()
    if len(config.token) < 32:
        raise HTTPException(503, detail={"code": "SANDBOX_UNAVAILABLE", "message": "Sandbox unavailable"})
    try:
        deadline = get_sandbox_limits(profile)["timeout"] + 40
        async with asyncio.timeout(deadline), httpx.AsyncClient(trust_env=False, timeout=deadline) as client:
            async with client.stream(
                    "POST", f"{config.endpoint.rstrip('/')}/execute",
                    headers={"Authorization": f"Bearer {config.token}"},
                    json={"code": code, "profile": profile, "language": language},
            ) as response:
                if response.status_code == 503:
                    # Контракт runner: Retry-After есть только при перегрузке.
                    if response.headers.get("Retry-After"):
                        raise HTTPException(503, detail={"code": "SANDBOX_BUSY", "message": "Sandbox busy"},
                                            headers={"Retry-After": "1"})
                    raise HTTPException(503, detail={"code": "SANDBOX_UNAVAILABLE", "message": "Sandbox unavailable"})
                response.raise_for_status()
                body = bytearray()
                async for chunk in response.aiter_bytes():
                    body.extend(chunk)
                    if len(body) > MAX_OUTPUT_BYTES * 6 + 4096:
                        raise ValueError("Runner response too large")
                return ExecutionResult.model_validate(json.loads(body))
    except (httpx.HTTPError, ValueError, TimeoutError):
        raise HTTPException(503, detail={"code": "SANDBOX_UNAVAILABLE", "message": "Sandbox unavailable"})
