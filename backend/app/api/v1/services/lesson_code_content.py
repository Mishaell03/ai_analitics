"""Сохранение Markdown и эталонов в существующие хранилища урока."""

import hashlib
import io
import json

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.exercises import CodeSolution, LessonCodeContentRequest, LessonCodeContentResponse
from app.core.config import settings
from app.core.markdown import MarkdownParser
from app.core.minio_url import minio_storage
from app.core.storage_paths import COURSE_CONTENT_BUCKET, lesson_content_path
from app.models.courses import CourseModule, Lesson
from app.models.exercises import ExerciseAnswer
from app.services.sandbox.config import SandboxSettings
from app.services.sandbox.transport import execute_code


def decode_solution(answer: str | None) -> dict | None:
    try:
        value = json.loads(answer)
    except (TypeError, ValueError):
        return None
    if isinstance(value, dict) and value.get("type") == "code" and "language" in value:
        return value
    return None


def validate_blocks(content: str, solutions: list[CodeSolution]):
    try:
        parsed = MarkdownParser().parse(content)
    except ValueError:
        raise HTTPException(422, detail="Invalid lesson exercise configuration") from None
    ids = set()
    code_blocks = {}
    for block in parsed.custom_blocks:
        if block.type not in {"test", "code"} or not block.data:
            continue
        exercise_id = block.data.get("exercise_id")
        if exercise_id and exercise_id in ids:
            raise HTTPException(422, detail="Duplicate exercise identifier")
        ids.add(exercise_id)
        if block.type == "code":
            code_blocks[exercise_id] = block.data["language"]
    submitted = {item.exercise_id: item.language for item in solutions}
    if len(submitted) != len(solutions) or submitted != code_blocks:
        raise HTTPException(422, detail="Code blocks and reference solutions must match")
    return parsed


class LessonCodeContentService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _snapshot(self, lesson_id: int, lock: bool = False):
        query = select(Lesson).where(Lesson.lesson_id == lesson_id)
        if lock:
            query = query.with_for_update()
        lesson = (await self.db.execute(query)).scalar_one_or_none()
        if lesson is None:
            raise HTTPException(404, detail="Lesson not found")
        module = (await self.db.execute(select(CourseModule).where(
            CourseModule.module_id == lesson.module_id,
        ))).scalar_one()
        path = lesson_content_path(module.course_id, module.module_id, lesson_id)
        raw = await minio_storage.get_text(file_path=path, bucket=COURSE_CONTENT_BUCKET,
                                           max_bytes=settings.max_text_file_size, strict=True)
        rows = (await self.db.execute(select(ExerciseAnswer).where(
            ExerciseAnswer.lesson_id == lesson_id,
        ).order_by(ExerciseAnswer.exercise_id))).scalars().all()
        # В версию входят и ответы: параллельная правка не теряется молча.
        version = hashlib.sha256(json.dumps([
            raw, [(row.exercise_id, row.answer) for row in rows],
        ], ensure_ascii=False).encode()).hexdigest()
        return path, raw, rows, version

    async def get(self, lesson_id: int) -> LessonCodeContentResponse:
        _, raw, rows, version = await self._snapshot(lesson_id)
        solutions = []
        for row in rows:
            value = decode_solution(row.answer)
            if value is not None:
                solutions.append(CodeSolution(exercise_id=row.exercise_id,
                                              language=value["language"], code=value["value"]))
        try:
            content = MarkdownParser().parse(raw or "").content
        except ValueError:
            raise HTTPException(409, detail="Invalid lesson exercise configuration") from None
        return LessonCodeContentResponse(content=content,
                                         solutions=solutions, version=version)

    async def save(self, lesson_id: int, data: LessonCodeContentRequest) -> LessonCodeContentResponse:
        validate_blocks(data.content, data.solutions)
        encoded = data.content.encode("utf-8")
        if len(encoded) > settings.lesson_content_max_upload_size:
            raise HTTPException(413, detail="Lesson content too large")
        path, raw, rows, version = await self._snapshot(lesson_id, lock=True)
        if data.version != version and not (data.version is None and raw is None and not rows):
            raise HTTPException(409, detail="Lesson changed; reload before saving")
        existing = {row.exercise_id: row for row in rows}
        executions = {}
        profiles = SandboxSettings().assignment_profiles
        for item in data.solutions:
            row = existing.get(item.exercise_id)
            if row is not None and decode_solution(row.answer) is None:
                raise HTTPException(409, detail="Identifier belongs to another exercise")
        # Исполняем до изменения строк и Markdown: отказ runner не сохраняет частичный результат.
        for item in data.solutions:
            executions[item.exercise_id] = await execute_code(
                code=item.code, profile=profiles.get(f"{lesson_id}:{item.exercise_id}", "light"),
                language=item.language,
            )
        next_ids = {item.exercise_id for item in data.solutions}
        for row in rows:
            if decode_solution(row.answer) is not None and row.exercise_id not in next_ids:
                await self.db.delete(row)
        for item in data.solutions:
            row = existing.get(item.exercise_id)
            if row is not None and decode_solution(row.answer) is None:
                raise HTTPException(409, detail="Identifier belongs to another exercise")
            if row is None:
                row = ExerciseAnswer(lesson_id=lesson_id, exercise_id=item.exercise_id)
                self.db.add(row)
            row.answer = json.dumps({"type": "code", "language": item.language,
                                     "value": item.code,
                                     "execution": executions[item.exercise_id].model_dump()}, ensure_ascii=False)
        await self.db.flush()
        # MinIO и PostgreSQL не поддерживают общую транзакцию. При ошибке
        # записи БД восстанавливаем прежний Markdown, не записывая туда эталоны.
        await minio_storage.put_stream(io.BytesIO(encoded), len(encoded), COURSE_CONTENT_BUCKET,
                                       path, "text/markdown")
        try:
            await self.db.commit()
        except Exception:
            await self.db.rollback()
            if raw is None:
                await minio_storage.delete_file(file_path=path, bucket=COURSE_CONTENT_BUCKET)
            else:
                previous = raw.encode("utf-8")
                await minio_storage.put_stream(io.BytesIO(previous), len(previous), COURSE_CONTENT_BUCKET,
                                               path, "text/markdown")
            raise
        return await self.get(lesson_id)
