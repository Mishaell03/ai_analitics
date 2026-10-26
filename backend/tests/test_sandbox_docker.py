"""ЯВНЫЕ INTEGRATION-ТЕСТЫ: SANDBOX_DOCKER_TESTS=1, ТОЛЬКО ГОТОВЫЙ ОБРАЗ."""

import asyncio
import json
import os
import secrets
import uuid

import httpx
import pytest

from app.services.sandbox.config import MAX_OUTPUT_BYTES, SandboxSettings
from app.services.sandbox.runner import SandboxBusy, SandboxRunner, create_app

pytestmark = pytest.mark.skipif(os.getenv("SANDBOX_DOCKER_TESTS") != "1", reason="Docker tests are opt-in")


@pytest.fixture(scope="module", autouse=True)
def require_idle_sandbox():
    # recovery-тест удаляет managed-контейнеры: не трогаем активные задания.
    runner = SandboxRunner(SandboxSettings())
    ids = asyncio.run(runner._docker("ps", "-aq", "--filter", "label=analytics.sandbox=1"))
    if ids:
        pytest.fail("Sandbox containers already exist; stop the runner and finish active jobs before testing")


async def execute_and_check_cleanup(code, profile="light"):
    runner = SandboxRunner(SandboxSettings())
    names = []
    original = runner.create_args

    def create_args(name, profile):
        names.append(name)
        return original(name, profile)

    runner.create_args = create_args
    try:
        return await runner.execute(code, profile)
    finally:
        for name in names:
            assert not await runner._docker("ps", "-aq", "--filter", f"name=^/{name}$")
        assert runner.active == 0


@pytest.mark.parametrize("code,expected", [
    ('print("hello")', "hello"),
    ('import numpy as np; print(np.arange(5).sum())', "10"),
    ('import pandas as pd; print(pd.Series([1, 2, 3]).sum())', "6"),
    ('import matplotlib; import matplotlib.pyplot as plt; '
     'plt.plot([1, 2]); plt.savefig("/tmp/plot.png"); print(matplotlib.get_backend())', "Agg"),
])
def test_python_libraries(code, expected):
    result = asyncio.run(execute_and_check_cleanup(code, "standard"))
    assert result.exit_code == 0, result
    assert expected.lower() in result.stdout.lower()
    assert not result.timed_out


def test_syntax_error():
    result = asyncio.run(execute_and_check_cleanup("if :"))
    assert result.exit_code != 0
    assert "SyntaxError" in result.stderr


def test_infinite_loop_timeout():
    result = asyncio.run(execute_and_check_cleanup("while True: pass"))
    assert result.timed_out
    assert result.exit_code != 0
    assert result.duration < 8


def test_memory_limit():
    result = asyncio.run(execute_and_check_cleanup("a = bytearray(1024 * 1024 * 1024)"))
    assert result.exit_code != 0
    assert result.memory_limited or "MemoryError" in result.stderr


def test_excessive_output():
    result = asyncio.run(execute_and_check_cleanup('while True: print("x" * 8192)'))
    assert result.output_limited
    assert len(result.stdout.encode()) + len(result.stderr.encode()) <= MAX_OUTPUT_BYTES
    assert not result.timed_out


def test_binary_output_is_bounded():
    result = asyncio.run(execute_and_check_cleanup('import os; os.write(1, b"\\xff" * 100000)'))
    assert result.output_limited
    assert len(result.stdout.encode()) + len(result.stderr.encode()) <= MAX_OUTPUT_BYTES


def test_live_container_security():
    async def scenario():
        runner = SandboxRunner(SandboxSettings())
        task = asyncio.create_task(runner.execute(
            'import os, socket, time\n'
            'assert os.getuid() == 65534\n'
            'assert not os.path.exists("/var/run/docker.sock")\n'
            'assert not any(k in os.environ for k in ["DB_PASSWORD", "MINIO_SECRET_KEY", "SANDBOX_RUNNER_TOKEN"])\n'
            'try:\n open("/work/forbidden", "w")\n'
            'except OSError: pass\n'
            'else: raise AssertionError("writable root")\n'
            's = socket.socket(); s.settimeout(0.2)\n'
            'try:\n s.connect(("1.1.1.1", 80))\n'
            'except OSError: pass\n'
            'else: raise AssertionError("network available")\n'
            'print("isolated", flush=True); time.sleep(2)', "light"))
        try:
            await asyncio.sleep(0.5)
            ids = (await runner._docker("ps", "-q", "--filter", "label=analytics.sandbox=1")).split()
            assert len(ids) == 1
            info = json.loads(await runner._docker("inspect", ids[0]))[0]
            host = info["HostConfig"]
            assert host["ReadonlyRootfs"] and host["NetworkMode"] == "none"
            assert host["CapDrop"] == ["ALL"]
            assert "no-new-privileges:true" in host["SecurityOpt"]
            assert host["Memory"] == 256 * 1024 * 1024
            assert host["MemorySwap"] == host["Memory"]
            assert host["NanoCpus"] == 250_000_000
            assert host["PidsLimit"] == 64
            assert host["LogConfig"]["Type"] == "none"
            assert not host["Binds"]
            assert host["Runtime"] == "runc"
            assert info["Config"]["User"] == "65534:65534"
            assert host["RestartPolicy"]["Name"] == "no"
            assert host["ShmSize"] == 8 * 1024 * 1024
            assert host["CgroupnsMode"] == "private"
            assert all(flag in host["Tmpfs"]["/tmp"] for flag in ("noexec", "nosuid", "nodev", "size=64m"))
            result = await task
            assert result.exit_code == 0, result
            assert "isolated" in result.stdout
            assert not await runner._docker("ps", "-aq", "--filter", f"id={ids[0]}")
        finally:
            if not task.done():
                task.cancel()
            await asyncio.gather(task, return_exceptions=True)
    asyncio.run(scenario())


def test_concurrent_requests_and_heavy_limit():
    async def scenario():
        runner = SandboxRunner(SandboxSettings())
        tasks = [asyncio.create_task(runner.execute("import time; time.sleep(2)", profile))
                 for profile in ("heavy", "light", "standard")]
        try:
            await asyncio.sleep(0.1)
            assert runner.active == 3
            with pytest.raises(SandboxBusy):
                await runner.execute("pass", "light")
            results = await asyncio.gather(*tasks)
            assert all(result.exit_code == 0 for result in results)
            heavy = asyncio.create_task(runner.execute("import time; time.sleep(1)", "heavy"))
            tasks.append(heavy)
            await asyncio.sleep(0.1)
            with pytest.raises(SandboxBusy):
                await runner.execute("pass", "heavy")
            assert (await heavy).exit_code == 0
        finally:
            for task in tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
        assert runner.active == runner.heavy_active == 0
    asyncio.run(scenario())


def test_cancellation_removes_container():
    async def scenario():
        runner = SandboxRunner(SandboxSettings())
        task = asyncio.create_task(runner.execute("while True: pass", "standard"))
        await asyncio.sleep(0.5)
        ids = (await runner._docker("ps", "-aq", "--filter", "label=analytics.sandbox=1")).split()
        assert ids
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
        for container_id in ids:
            assert not await runner._docker("ps", "-aq", "--filter", f"id={container_id}")
        assert runner.active == 0
    asyncio.run(scenario())


def test_student_cannot_bypass_deadline_by_killing_timer():
    # timeout внутри контейнера — дополнительная защита, а не доверенный таймер:
    # процесс ученика имеет тот же uid. Внешний runner всё равно обязан убить его.
    result = asyncio.run(execute_and_check_cleanup(
        "import os, signal\nos.kill(os.getppid(), signal.SIGKILL)\nwhile True: pass"))
    assert result.exit_code != 0
    assert result.duration < 8


def test_http_runner_and_single_owner(monkeypatch):
    monkeypatch.setenv("SANDBOX_RUNNER_TOKEN", "t" * 32)
    # Временные файлы этого теста остаются внутри проекта.
    monkeypatch.setenv("SANDBOX_LOCK_FILE", ".sandbox-runner.lock")

    async def scenario():
        app = create_app()
        async with app.router.lifespan_context(app):
            other = create_app()
            with pytest.raises(BlockingIOError):
                async with other.router.lifespan_context(other):
                    pass
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://runner") as client:
                headers = {"Authorization": "Bearer " + "t" * 32}
                tasks = [asyncio.create_task(client.post("/execute", headers=headers,
                         json={"code": "import time; time.sleep(2); print(42)", "profile": "light"})) for _ in range(3)]
                await asyncio.sleep(0.2)
                busy = await client.post("/execute", headers=headers, json={"code": "pass", "profile": "standard"})
                assert busy.status_code == 503
                responses = await asyncio.gather(*tasks)
                assert all(response.status_code == 200 and response.json()["stdout"] == "42\n" for response in responses)
    asyncio.run(scenario())


def test_recovery_removes_crashed_runner_container():
    async def scenario():
        runner = SandboxRunner(SandboxSettings())
        name = "analytics-sandbox-recovery-test"
        try:
            await runner._docker(*runner.create_args(name, "light"))
            await runner._docker("start", name)
            await runner.recover(startup=True)
            assert not await runner._docker("ps", "-aq", "--filter", f"name=^/{name}$")
        finally:
            await runner.remove(name)
    asyncio.run(scenario())


@pytest.mark.skipif(not os.getenv("SANDBOX_RUNNER_TEST_IMAGE"), reason="Built runner image is optional")
def test_built_runner_service():
    """Реальный отдельный процесс: проверяет packaging, CLI и доступ к daemon."""
    async def scenario():
        runner = SandboxRunner(SandboxSettings())
        name = f"analytics-runner-test-{uuid.uuid4().hex}"
        token = secrets.token_hex(32)
        socket = os.getenv("SANDBOX_DOCKER_SOCKET", "/var/run/docker.sock")
        try:
            await runner._docker(
                "run", "--detach", "--pull=never", "--name", name,
                "--network", "none", "--read-only", "--cap-drop", "ALL",
                "--security-opt", "no-new-privileges:true",
                "--tmpfs", "/tmp:size=32m,noexec,nosuid,nodev",
                "--mount", f"type=bind,source={socket},target=/var/run/docker.sock",
                "--env", f"SANDBOX_RUNNER_TOKEN={token}",
                "--env", "SANDBOX_LOCK_FILE=/tmp/runner.lock",
                "--env", f"SANDBOX_IMAGE={runner.config.image}",
                "--env", f"SANDBOX_RUNTIME={runner.config.runtime}",
                os.environ["SANDBOX_RUNNER_TEST_IMAGE"],
            )
            # HTTP остаётся внутри runner; ни порт, ни socket студента не публикуется.
            script = '''
import httpx, time
for attempt in range(30):
    try:
        denied = httpx.post("http://127.0.0.1:8090/execute", json={"code": "pass", "profile": "light"})
        break
    except httpx.ConnectError:
        time.sleep(0.1)
else:
    raise AssertionError("Runner did not start")
assert denied.status_code == 401, denied.text
import os
result = httpx.post("http://127.0.0.1:8090/execute",
    headers={"Authorization": "Bearer " + os.environ["SANDBOX_RUNNER_TOKEN"]},
    json={"code": "import numpy as np; print(np.arange(5).sum())", "profile": "standard"}, timeout=35)
assert result.status_code == 200, result.text
assert result.json()["stdout"] == "10\\n", result.text
assert result.json()["exit_code"] == 0, result.text
print("runner service OK")
'''
            assert await runner._docker("exec", name, "python", "-c", script) == "runner service OK"
            assert not await runner._docker("ps", "-aq", "--filter", "label=analytics.sandbox=1")
        finally:
            await runner.remove(name)
    asyncio.run(scenario())
