"""Кодовые блоки: проверки и сохранение без внешней БД/MinIO."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import httpx
import pytest
from fastapi import FastAPI, HTTPException

from app.api.v1.routes.exercises import router
from app.api.v1.schemas.exercises import CodeSolution, LessonCodeContentRequest
from app.api.v1.services import lesson_code_content as module
from app.api.v1.services.lesson_code_content import LessonCodeContentService, validate_blocks
from app.api.v1.services.exercise_answers import ExerciseAnswerService
from app.api.v1.services.exercise_check import ExerciseCheckService
from app.api.v1.schemas.exercise_check import ExerciseCheckRequest
from app.api.v1.schemas.sandbox import ExecutionResult
from app.api.v1.services.lesson_content import LessonContentService
from app.api.v1.services.lesson_admin import LessonAdminService
from app.api.v1.services.lesson_completion import LessonCompletionService
from app.api.v1.services.student_exercises import StudentExerciseService
from app.core.database import get_db
from app.core.markdown import MarkdownParser
from app.core.session import get_current_admin
from app.core.backend_error_logs import sanitize_request_body

SOURCE = ":::code python\nid: stable\n:::\n"
SECRET = "print('TEACHER_SECRET')"


@pytest.fixture(autouse=True)
def runner(monkeypatch):
    execute = AsyncMock(return_value=ExecutionResult(
        stdout="TEACHER_SECRET\n", stderr="", exit_code=0, timed_out=False, duration=0.1,
    ))
    monkeypatch.setattr(module, "execute_code", execute)
    return execute


def solution(language="python", exercise_id="stable"):
    return CodeSolution(exercise_id=exercise_id, language=language, code=SECRET)


@pytest.mark.parametrize("language", ["python", "sql"])
def test_code_blocks_use_existing_exercise_contract(language):
    parsed = validate_blocks(SOURCE.replace("python", language), [solution(language)])
    assert parsed.custom_blocks[0].data == {
        "exercise_id": "stable", "language": language, "body": "",
    }
    assert SECRET not in parsed.content
    assert LessonCompletionService.get_exercise_ids(parsed.custom_blocks) == {"stable"}


@pytest.mark.parametrize("source,solutions", [
    (SOURCE, []), (SOURCE, [solution("sql")]), (SOURCE, [solution(exercise_id="other")]),
    (SOURCE, [solution(), solution()]), (SOURCE * 2, [solution()]),
    (SOURCE + ":::test\nid: stable\nQuestion\n:::", [solution()]),
    (SOURCE.replace("python", "ruby"), [solution()]),
    (SOURCE.replace("id: stable", "id: reference"), [solution(exercise_id="reference")]),
    (SOURCE.replace("id: stable", "id: stable\n" + SECRET), [solution()]),
    (SOURCE.replace("id: stable", "id: stable\n<script>secret</script>"), [solution()]),
    (":::code python\nid: stable", [solution()]),
])
def test_invalid_relationships_rejected(source, solutions):
    with pytest.raises(HTTPException) as exc:
        validate_blocks(source, solutions)
    assert exc.value.status_code == 422


def test_fenced_example_is_not_an_exercise():
    parsed = validate_blocks("```md\n" + SOURCE + "```", [])
    assert not parsed.custom_blocks


def test_save_keeps_secret_in_database_only_and_cleans_removed_blocks(monkeypatch):
    old = SimpleNamespace(exercise_id="removed", answer=json.dumps({
        "type": "code", "language": "sql", "value": "OLD_SECRET",
    }))
    db = SimpleNamespace(add=Mock(), delete=AsyncMock(), flush=AsyncMock(), commit=AsyncMock())
    service = LessonCodeContentService(db)
    service._snapshot = AsyncMock(return_value=("lesson.md", "previous", [old], "a" * 64))
    service.get = AsyncMock(return_value="saved")
    upload = AsyncMock()
    monkeypatch.setattr(module.minio_storage, "put_stream", upload)
    data = LessonCodeContentRequest(content=SOURCE, solutions=[solution()], version="a" * 64)
    assert asyncio.run(service.save(1, data)) == "saved"
    row = db.add.call_args.args[0]
    assert json.loads(row.answer)["value"] == SECRET
    assert json.loads(row.answer)["execution"]["stdout"] == "TEACHER_SECRET\n"
    assert json.loads(row.answer)["execution"]["success"] is True
    assert row.lesson_id == 1 and row.exercise_id == "stable"
    assert upload.call_args.args[0].getvalue().decode() == SOURCE
    assert SECRET not in upload.call_args.args[0].getvalue().decode()
    db.delete.assert_awaited_once_with(old)
    db.commit.assert_awaited_once()


def test_stale_editor_cannot_overwrite_content(monkeypatch):
    service = LessonCodeContentService(None)
    service._snapshot = AsyncMock(return_value=("lesson.md", SOURCE, [], "b" * 64))
    upload = AsyncMock()
    monkeypatch.setattr(module.minio_storage, "put_stream", upload)
    data = LessonCodeContentRequest(content=SOURCE, solutions=[solution()], version="a" * 64)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.save(1, data))
    assert exc.value.status_code == 409
    upload.assert_not_awaited()


def test_runner_unavailable_does_not_change_content(monkeypatch, runner):
    runner.side_effect = HTTPException(503, detail="Sandbox unavailable")
    db = SimpleNamespace(add=Mock(), delete=AsyncMock(), flush=AsyncMock(), commit=AsyncMock())
    service = LessonCodeContentService(db)
    service._snapshot = AsyncMock(return_value=("lesson.md", "previous", [], "a" * 64))
    upload = AsyncMock()
    monkeypatch.setattr(module.minio_storage, "put_stream", upload)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.save(1, LessonCodeContentRequest(
            content=SOURCE, solutions=[solution()], version="a" * 64,
        )))
    assert exc.value.status_code == 503
    db.add.assert_not_called()
    db.delete.assert_not_awaited()
    db.commit.assert_not_awaited()
    upload.assert_not_awaited()


def test_reference_execution_error_is_saved(monkeypatch, runner):
    runner.return_value = ExecutionResult(
        stdout="", stderr="ValueError", exit_code=1, timed_out=False, duration=0.1,
    )
    db = SimpleNamespace(add=Mock(), flush=AsyncMock(), commit=AsyncMock())
    service = LessonCodeContentService(db)
    service._snapshot = AsyncMock(return_value=("lesson.md", "previous", [], "a" * 64))
    service.get = AsyncMock()
    monkeypatch.setattr(module.minio_storage, "put_stream", AsyncMock())
    asyncio.run(service.save(1, LessonCodeContentRequest(
        content=SOURCE, solutions=[solution()], version="a" * 64,
    )))
    result = json.loads(db.add.call_args.args[0].answer)["execution"]
    assert result["success"] is False
    assert result["stderr"] == "ValueError"
    db.commit.assert_awaited_once()


def test_database_failure_restores_previous_markdown(monkeypatch):
    db = SimpleNamespace(add=Mock(), flush=AsyncMock(), commit=AsyncMock(side_effect=RuntimeError()),
                         rollback=AsyncMock())
    service = LessonCodeContentService(db)
    service._snapshot = AsyncMock(return_value=("lesson.md", "previous", [], "a" * 64))
    upload = AsyncMock()
    monkeypatch.setattr(module.minio_storage, "put_stream", upload)
    with pytest.raises(RuntimeError):
        asyncio.run(service.save(1, LessonCodeContentRequest(
            content=SOURCE, solutions=[solution()], version="a" * 64,
        )))
    assert upload.await_count == 2
    assert upload.call_args.args[0].getvalue() == b"previous"
    db.rollback.assert_awaited_once()


def test_student_contract_has_no_reference_fields():
    parsed = MarkdownParser().parse(SOURCE)
    service = StudentExerciseService(None)
    service.get_lesson_content = AsyncMock(return_value=SimpleNamespace(
        custom_blocks=parsed.custom_blocks, completed_exercises={},
    ))
    current = SimpleNamespace(user=SimpleNamespace(user_id=1), session=SimpleNamespace(
        language="en", device_id="d", id=1, platform="web",
    ))
    exercises = asyncio.run(service.list_exercises(object(), "course", 1, 1, current))
    assert set(exercises[0].model_dump()) == {
        "exercise_id", "language", "body", "execution_enabled", "is_completed", "expert_solution_available",
    }
    assert SECRET not in exercises[0].model_dump_json()


def test_references_are_redacted_in_error_logs():
    sanitized = sanitize_request_body(json.dumps({"solutions": [solution().model_dump()],
                                                   "answer": SECRET, "code": SECRET}))
    assert SECRET not in sanitized


def test_legacy_answer_endpoint_cannot_overwrite_managed_solution():
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(
        scalar_one_or_none=lambda: json.dumps({"type": "code", "language": "python", "value": SECRET}),
    )))
    with pytest.raises(HTTPException) as exc:
        asyncio.run(ExerciseAnswerService(db)._guard_code_answer(1, "stable", "replacement"))
    assert exc.value.status_code == 409


def test_presigned_upload_cannot_bypass_managed_solution_sync():
    expected = json.dumps({"type": "code", "language": "python", "value": SECRET})
    db = SimpleNamespace(execute=AsyncMock(return_value=SimpleNamespace(
        scalars=lambda: SimpleNamespace(all=lambda: [expected]),
    )))
    service = LessonAdminService(db)
    service._get_course_admin = AsyncMock(return_value=SimpleNamespace(course_id=1))
    service._get_module_admin = AsyncMock(return_value=SimpleNamespace(course_id=1, module_id=1))
    service._get_lesson_admin = AsyncMock(return_value=SimpleNamespace(lesson_id=1))
    service._build_upload = AsyncMock()
    with pytest.raises(HTTPException) as exc:
        asyncio.run(service.get_lesson_upload_url(object(), "course", 1, 1, "en"))
    assert exc.value.status_code == 409
    service._build_upload.assert_not_awaited()


@pytest.mark.parametrize("source,passes", [
    (SOURCE, True), (SOURCE.replace("python", "sql"), False), ("", False), (SOURCE * 2, False),
])
def test_code_check_validates_current_block_without_disclosing_reference(monkeypatch, source, passes):
    expected = json.dumps({"type": "code", "language": "python", "value": SECRET})
    db = SimpleNamespace(execute=AsyncMock(side_effect=[
        SimpleNamespace(scalar_one_or_none=lambda: 1),
        SimpleNamespace(scalar_one_or_none=lambda: expected),
    ]), add=Mock(), commit=AsyncMock())
    service = ExerciseCheckService(db)
    service._get_course = AsyncMock(return_value=SimpleNamespace(course_id=1))
    service._get_module = AsyncMock(return_value=SimpleNamespace(module_id=1))
    service._get_lesson = AsyncMock(return_value=SimpleNamespace(lesson_id=1))
    monkeypatch.setattr(LessonContentService, "_read_content", AsyncMock(return_value=SimpleNamespace(
        custom_blocks=MarkdownParser().parse(source).custom_blocks,
    )))
    call = service.check_answer(object(), "course", 1, 1, "stable",
                                ExerciseCheckRequest(answer=SECRET), "en", user_id=1)
    with pytest.raises(HTTPException) as exc:
        asyncio.run(call)
    assert exc.value.status_code == 422
    assert exc.value.detail["code"] == "CODE_EXECUTION_REQUIRED"
    assert SECRET not in str(exc.value.detail)
    db.add.assert_not_called()


@pytest.mark.parametrize("method", ["GET", "PUT"])
@pytest.mark.parametrize("status", [401, 403])
def test_code_content_routes_require_admin(method, status):
    app = FastAPI()
    app.include_router(router)
    app.dependency_overrides[get_db] = lambda: None

    async def denied():
        raise HTTPException(status)

    app.dependency_overrides[get_current_admin] = denied

    async def scenario():
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
            response = await client.request(method, "/admin/lessons/1/code-content", json={
                "content": SOURCE, "solutions": [solution().model_dump()],
            })
        assert response.status_code == status
        assert SECRET not in response.text

    asyncio.run(scenario())
