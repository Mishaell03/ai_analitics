"""Docker доступен только этому процессу, не основному приложению FastAPI."""

import asyncio
import fcntl
import json
import logging
import time
import uuid
from contextlib import asynccontextmanager, suppress
from secrets import compare_digest

from fastapi import Depends, FastAPI, Header, HTTPException

from app.api.v1.schemas.sandbox import ExecutionResult, RunnerExecutionRequest
from app.services.sandbox.config import MANAGED_LABEL, MAX_OUTPUT_BYTES, SandboxSettings, get_sandbox_limits
from app.services.sandbox.plots import MAX_PLOT_WIRE_BYTES, extract_plot_output, python_with_plots

logger = logging.getLogger(__name__)


def decode_output(data: bytearray, limit: int) -> str:
    text = data.decode("utf-8", errors="replace").encode("utf-8")
    return text[:limit].decode("utf-8", errors="ignore")


class SandboxBusy(Exception):
    pass


class SandboxUnavailable(Exception):
    pass


class SandboxRunner:
    def __init__(self, config: SandboxSettings):
        self.config = config
        self.active = 0
        self.heavy_active = 0
        self.healthy = True
        self.pending_cleanup: set[str] = set()

    async def _docker(self, *args: str) -> str:
        process = await asyncio.create_subprocess_exec(
            "docker", *args, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        try:
            stdout, stderr = await asyncio.wait_for(process.communicate(), timeout=10)
            if process.returncode:
                raise SandboxUnavailable(stderr.decode("utf-8", errors="replace")[:1024])
            return stdout.decode("utf-8", errors="replace").strip()
        except TimeoutError:
            raise SandboxUnavailable("Docker operation timed out") from None
        finally:
            if process.returncode is None:
                with suppress(ProcessLookupError):
                    process.kill()
                # communicate осушает pipes, даже если предыдущий вызов отменён.
                await process.communicate()

    async def remove(self, name: str):
        try:
            await self._docker("rm", "--force", name)
        except SandboxUnavailable:
            # rm может вернуть ошибку, если create не успел создать контейнер.
            names = (await self._docker("ps", "-aq", "--filter", f"name=^/{name}$")).split()
            if names:
                raise
        self.pending_cleanup.discard(name)

    async def recover(self, *, startup: bool = False):
        """Удаляет остатки после аварии; просроченные контейнеры — при работе."""
        ids = (await self._docker("ps", "-aq", "--filter", f"label={MANAGED_LABEL}")).split()
        for container_id in ids:
            info = json.loads(await self._docker("inspect", container_id))[0]
            deadline = float(info["Config"]["Labels"].get("analytics.deadline", "0"))
            if startup or time.time() > deadline:
                await self.remove(container_id)
        for name in tuple(self.pending_cleanup):
            await self.remove(name)
        self.healthy = True

    async def watch(self):
        while True:
            await asyncio.sleep(1)
            try:
                await self.recover()
            except Exception:
                was_healthy = self.healthy
                self.healthy = False
                if was_healthy:
                    logger.exception("Sandbox cleanup watchdog failed")

    def create_args(self, name: str, profile: str) -> list[str]:
        limits = get_sandbox_limits(profile)
        return [
            "create", "--pull=never", "--name", name,
            "--label", MANAGED_LABEL,
            "--label", f"analytics.deadline={time.time() + limits['timeout'] + 15}",
            "--runtime", self.config.runtime, "--network", "none", "--read-only",
            "--user", "65534:65534", "--cap-drop", "ALL",
            "--security-opt", "no-new-privileges:true", "--init",
            "--restart", "no", "--stop-timeout", "0",
            "--cpus", str(limits["cpu"]), "--memory", limits["memory"],
            "--memory-swap", limits["memory"], "--pids-limit", "64",
            "--shm-size", "8m", "--ipc", "private", "--cgroupns", "private",
            "--ulimit", "nofile=128:128", "--ulimit", "core=0:0",
            "--ulimit", "fsize=16777216:16777216",
            "--tmpfs", "/tmp:rw,noexec,nosuid,nodev,size=64m,mode=1777",
            "--log-driver", "none", "--env", "MPLBACKEND=Agg", "--interactive",
            "--entrypoint", "timeout", self.config.image,
            "--signal=KILL", str(limits["timeout"]), "python", "-B", "-",
        ]

    async def execute(self, code: str, profile: str) -> ExecutionResult:
        limits = get_sandbox_limits(profile)
        # Повторная проверка нужна и для прямых вызовов, не только HTTP.
        RunnerExecutionRequest(code=code, profile=profile)
        if not self.healthy:
            raise SandboxUnavailable("Runner cleanup is unhealthy")
        if self.active >= self.config.concurrency or (
                profile == "heavy" and self.heavy_active >= self.config.heavy_concurrency
        ):
            raise SandboxBusy()
        # До первого await: атомарное принятие в одном event loop отдельного runner.
        self.active += 1
        self.heavy_active += profile == "heavy"
        name = f"analytics-sandbox-{uuid.uuid4().hex}"
        started = time.monotonic()
        process = None
        tasks = []
        stdout, stderr = bytearray(), bytearray()
        output_limited = False
        timed_out = False

        async def read_output(stream, target):
            nonlocal output_limited
            while chunk := await stream.read(8192):
                available = MAX_OUTPUT_BYTES + MAX_PLOT_WIRE_BYTES - len(stdout) - len(stderr)
                target.extend(chunk[:available])
                if len(chunk) > available:
                    output_limited = True
                    # Продолжаем осушать pipe без накопления: иначе wait()
                    # Docker CLI может зависнуть на заполненном stderr/stdout.

        async def run():
            nonlocal process, tasks
            await self._docker(*self.create_args(name, profile))
            process = await asyncio.create_subprocess_exec(
                "docker", "start", "--attach", "--interactive", name,
                stdin=asyncio.subprocess.PIPE, stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            tasks = [asyncio.create_task(read_output(process.stdout, stdout)),
                     asyncio.create_task(read_output(process.stderr, stderr))]
            process.stdin.write(python_with_plots(code).encode("utf-8"))
            with suppress(BrokenPipeError, ConnectionResetError):
                await process.stdin.drain()
            process.stdin.close()
            while process.returncode is None and not output_limited:
                await asyncio.sleep(0.02)
            if output_limited:
                with suppress(SandboxUnavailable):
                    await self._docker("kill", name)
            await process.wait()
            await asyncio.gather(*tasks)

        try:
            try:
                await asyncio.wait_for(run(), timeout=limits["timeout"] + 1)
            except TimeoutError:
                timed_out = True
                with suppress(SandboxUnavailable):
                    await self._docker("kill", name)
            state = json.loads(await self._docker("inspect", "--format", "{{json .State}}", name))
            if state.get("Error") or state.get("Status") not in {"exited", "dead"}:
                raise SandboxUnavailable("Container failed to start")
            elapsed = time.monotonic() - started
            timed_out = timed_out or (
                state["ExitCode"] == 137 and not state.get("OOMKilled")
                and elapsed >= limits["timeout"]
            )
            # Невалидный UTF-8 заменяется безопасно, но replacement-символ
            # занимает три байта: ограничиваем и окончательный ответ.
            text_output, plots, plots_limited, chart_data = extract_plot_output(bytes(stdout))
            output_limited = output_limited or plots_limited or len(text_output) + len(stderr) > MAX_OUTPUT_BYTES
            stdout_text = decode_output(bytearray(text_output), MAX_OUTPUT_BYTES)
            remaining = MAX_OUTPUT_BYTES - len(stdout_text.encode("utf-8"))
            stderr_text = decode_output(stderr, remaining)
            return ExecutionResult(
                stdout=stdout_text, stderr=stderr_text,
                exit_code=state["ExitCode"], timed_out=timed_out,
                duration=round(elapsed, 3), output_limited=output_limited,
                memory_limited=state.get("OOMKilled", False),
                plots=plots,
                chart_data=chart_data,
            )
        finally:
            async def cleanup():
                try:
                    await self.remove(name)
                except Exception:
                    self.healthy = False
                    self.pending_cleanup.add(name)
                    logger.exception("Sandbox container cleanup failed")
                finally:
                    try:
                        for task in tasks:
                            task.cancel()
                        await asyncio.gather(*tasks, return_exceptions=True)
                        if process is not None:
                            if process.returncode is None:
                                with suppress(ProcessLookupError):
                                    process.kill()
                            # При отмене run() readers могли быть отменены
                            # вместе с gather(). Осушаем pipes перед wait().
                            await asyncio.gather(
                                process.wait(), read_output(process.stdout, stdout),
                                read_output(process.stderr, stderr),
                            )
                    finally:
                        self.active -= 1
                        self.heavy_active -= profile == "heavy"
            # Отключение клиента/отмена запроса не отменяет удаление контейнера.
            cleanup_task = asyncio.create_task(cleanup())
            await asyncio.shield(cleanup_task)


def create_app(config: SandboxSettings | None = None) -> FastAPI:
    from app.services.sandbox.sql_runner import SQLRunner

    config = config or SandboxSettings()
    runner = SandboxRunner(config)
    sql_runner = SQLRunner(config)

    @asynccontextmanager
    async def lifespan(app):
        if len(config.token) < 32:
            raise RuntimeError("SANDBOX_RUNNER_TOKEN must contain at least 32 characters")
        # Один владелец Docker на общий volume, даже при ошибочном --workers 2.
        with open(config.lock_file, "a") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            try:
                await runner.recover(startup=True)
            except (SandboxUnavailable, OSError):
                # SQL не зависит от Docker. Watchdog восстановит Python после
                # запуска Docker/исправления доступа к сокету.
                runner.healthy = False
                logger.exception("Python sandbox unavailable at startup; SQL runner remains available")
            watchdog = asyncio.create_task(runner.watch())
            try:
                yield
            finally:
                watchdog.cancel()
                await asyncio.gather(watchdog, return_exceptions=True)
                with suppress(SandboxUnavailable, OSError):
                    await runner.recover(startup=True)

    app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)
    app.state.runner = runner
    app.state.sql_runner = sql_runner

    async def authenticate(authorization: str = Header(default="")):
        if len(config.token) < 32 or not compare_digest(
                authorization.encode("utf-8"), f"Bearer {config.token}".encode("utf-8")
        ):
            raise HTTPException(401, detail="Unauthorized")

    @app.post("/execute", response_model=ExecutionResult, dependencies=[Depends(authenticate)])
    async def execute(data: RunnerExecutionRequest):
        try:
            if data.language == "sql":
                return await sql_runner.execute(data.code)
            return await runner.execute(data.code, data.profile)
        except SandboxBusy:
            raise HTTPException(503, detail="Sandbox busy", headers={"Retry-After": "1"})
        except Exception:
            logger.exception("Sandbox execution failed")
            raise HTTPException(503, detail="Sandbox unavailable")

    # Лимит тела проверяется потоково до JSON parsing, включая chunked-запросы.
    from app.services.sandbox.transport import SandboxBodyLimitMiddleware
    app.add_middleware(SandboxBodyLimitMiddleware)
    return app
