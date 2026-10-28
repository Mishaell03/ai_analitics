"""Наставник урока: проверка доступа, история, квоты, краткая память и аудит."""

import asyncio
import logging
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert

from app.api.v1.schemas.ai import AIHistoryResponse, AIMessageResponse, AIQuestionRequest
from app.api.v1.services.lesson_content import LessonContentService
from app.models.ai import AIAnswer, AIConversation, AIQuestion
from app.services.llm.config import LLMSettings, brief_context, system_context
from app.services.llm.deepseek import MentorResult, OUTPUT_INSTRUCTIONS, UNAVAILABLE, generate
from app.services.llm.memory import (
    HISTORY_ANSWER_CHARS, HISTORY_QUESTION_CHARS, HISTORY_TURNS, LESSON_CHARS,
    compact_context, context_fingerprint, lesson_excerpt, memory_matches,
)

LEASE_SECONDS = 90
logger = logging.getLogger(__name__)


def message(question: AIQuestion, answer: AIAnswer | None) -> AIMessageResponse:
    return AIMessageResponse(
        question_id=question.question_id, request_id=question.request_id,
        question=question.question, user_context=question.user_context,
        answer=answer.answer if answer else None, status=question.status, created_at=question.created_at,
        error_code=answer.error_code if answer else None,
    )


class LessonAIService(LessonContentService):
    async def _access(self, request, course_slug, module_id, lesson_id, current):
        error = self._error(
            language=current.session.language, device_id=current.session.device_id,
            session_id=current.session.id, user_id=current.user.user_id, platform=current.session.platform,
        )
        course = await self._get_course(request=request, course_slug=course_slug, error=error)
        module = await self._get_module(request=request, course=course, module_id=module_id, error=error)
        lesson = await self._get_lesson(request=request, module=module, lesson_id=lesson_id, error=error)
        if not await self._is_enrolled(current.user.user_id, course.course_id):
            await self._raise(request=request, code="COURSE_ACCESS_REQUIRED", error=error)
        return course, module, lesson, error

    async def history(self, request, course_slug, module_id, lesson_id, current, after_id=0, limit=10):
        await self._access(request, course_slug, module_id, lesson_id, current)
        limit = min(limit, HISTORY_TURNS)
        latest_ids = (select(AIQuestion.question_id)
                      .join(AIConversation, AIConversation.conversation_id == AIQuestion.conversation_id)
                      .where(AIConversation.user_id == current.user.user_id, AIConversation.lesson_id == lesson_id)
                      .order_by(AIQuestion.question_id.desc()).limit(HISTORY_TURNS).correlate(None))
        rows = (await self.db.execute(
            select(AIQuestion, AIAnswer)
            .join(AIConversation, AIConversation.conversation_id == AIQuestion.conversation_id)
            .outerjoin(AIAnswer, AIAnswer.question_id == AIQuestion.question_id)
            .where(AIConversation.user_id == current.user.user_id, AIConversation.lesson_id == lesson_id,
                   AIQuestion.question_id > after_id, AIQuestion.question_id.in_(latest_ids))
            .order_by(AIQuestion.question_id).limit(limit + 1)
        )).all()
        return AIHistoryResponse(
            messages=[message(question, answer) for question, answer in rows[:limit]],
            next_after_id=rows[limit - 1][0].question_id if len(rows) > limit else None,
        )

    async def _expire(self, conversation, now):
        if not conversation.active_request or (conversation.busy_until and conversation.busy_until > now):
            return
        question = (await self.db.execute(select(AIQuestion).where(
            AIQuestion.conversation_id == conversation.conversation_id,
            AIQuestion.request_id == conversation.active_request,
            AIQuestion.status == "pending",
        ))).scalar_one_or_none()
        if question is not None:
            question.status = "failed"
            self.db.add(AIAnswer(question_id=question.question_id, answer=UNAVAILABLE, error_code="AI_REQUEST_EXPIRED"))
            await self.db.flush()
        conversation.active_request = None
        conversation.busy_until = None

    async def ask(self, request, course_slug, module_id, lesson_id, current, data: AIQuestionRequest):
        course, module, lesson, error = await self._access(request, course_slug, module_id, lesson_id, current)
        try:
            config, system, shared_context = LLMSettings(), system_context(), brief_context()
        except (OSError, ValueError):
            raise HTTPException(503, detail={"code": "AI_NOT_CONFIGURED", "message": "AI unavailable"}) from None

        # Short global acceptance lock: project quotas also hold across users/workers.
        locked = (await self.db.execute(select(func.pg_try_advisory_xact_lock(0x414951, 0)))).scalar_one()
        if not locked:
            raise HTTPException(409, detail={"code": "AI_REQUEST_IN_PROGRESS", "message": "Another AI request is being accepted"})
        await self.db.execute(insert(AIConversation).values(
            user_id=current.user.user_id, lesson_id=lesson_id,
        ).on_conflict_do_nothing(index_elements=["user_id", "lesson_id"]))
        conversation = (await self.db.execute(select(AIConversation).where(
            AIConversation.user_id == current.user.user_id, AIConversation.lesson_id == lesson_id,
        ).with_for_update().execution_options(populate_existing=True))).scalar_one()
        now = datetime.now(timezone.utc)
        await self._expire(conversation, now)
        existing = (await self.db.execute(select(AIQuestion, AIAnswer).outerjoin(
            AIAnswer, AIAnswer.question_id == AIQuestion.question_id,
        ).where(AIQuestion.conversation_id == conversation.conversation_id,
                AIQuestion.request_id == data.request_id))).one_or_none()
        if existing:
            question, answer = existing
            if question.question != data.question or question.user_context != data.user_context:
                raise HTTPException(409, detail={"code": "AI_REQUEST_ID_CONFLICT", "message": "Request ID already used"})
            response = message(question, answer)
            await self.db.commit()
            return response
        if conversation.active_request:
            raise HTTPException(409, detail={"code": "AI_REQUEST_IN_PROGRESS", "message": "Wait for the previous answer"})

        counts = (await self.db.execute(select(
            func.count(AIQuestion.question_id),
            func.count(AIQuestion.question_id).filter(AIQuestion.created_at > now - timedelta(minutes=1)),
        ).join(AIConversation, AIConversation.conversation_id == AIQuestion.conversation_id).where(
            AIConversation.user_id == current.user.user_id,
            AIQuestion.created_at > now - timedelta(days=1),
        ))).one()
        if counts[0] >= config.daily_limit or counts[1] >= config.minute_limit:
            raise HTTPException(429, detail={"code": "AI_QUOTA_EXCEEDED", "message": "AI request quota exceeded"},
                                headers={"Retry-After": "60"})

        project_counts = (await self.db.execute(select(
            func.count(AIQuestion.question_id),
            func.count(AIQuestion.question_id).filter(AIQuestion.created_at > now - timedelta(minutes=1)),
        ).where(AIQuestion.created_at > now - timedelta(days=1)))).one()
        if project_counts[0] >= config.project_daily_limit or project_counts[1] >= config.project_minute_limit:
            raise HTTPException(429, detail={"code": "AI_PROJECT_QUOTA_EXCEEDED", "message": "Project AI quota exceeded"},
                                headers={"Retry-After": "60"})

        content = await self._read_content(request=request, lesson=lesson, course_id=course.course_id, error=error)
        metadata = {
            "course": {"title": course.title[:200], "description": (course.description or "")[:300]},
            "module": module.title[:200], "lesson_title": lesson.title[:200],
            "brief_context": shared_context,
        }
        fingerprint = context_fingerprint(system + OUTPUT_INSTRUCTIONS, metadata, content.content, config.model)
        use_memory = memory_matches(conversation.provider_state, fingerprint)
        recent = []
        if use_memory:
            recent = (await self.db.execute(select(AIQuestion.question, AIAnswer.answer).join(
                AIAnswer, AIAnswer.question_id == AIQuestion.question_id,
            ).where(AIQuestion.conversation_id == conversation.conversation_id, AIQuestion.status == "completed",
                    AIQuestion.prompt_hash == fingerprint, AIQuestion.model == config.model)
                .order_by(AIQuestion.question_id.desc()).limit(HISTORY_TURNS))).all()
        context = {
            "course": metadata["course"], "module": metadata["module"],
            "brief_context": shared_context,
            "lesson": {"title": metadata["lesson_title"], "text": lesson_excerpt(content.content, data.question),
                       "text_truncated": len(content.content) > LESSON_CHARS},
            "summary": conversation.summary[:1000] if use_memory else "",
            "history": [{"question": q[:HISTORY_QUESTION_CHARS], "answer": a[:HISTORY_ANSWER_CHARS]}
                        for q, a in reversed(recent)],
            "question": data.question, "student_context": data.user_context,
        }
        context = compact_context(context, system + "\n" + OUTPUT_INSTRUCTIONS, config.max_input_bytes)
        question = AIQuestion(
            conversation_id=conversation.conversation_id, request_id=data.request_id,
            question=data.question, user_context=data.user_context, context_snapshot=context,
            prompt_hash=fingerprint,
            model=config.model, status="pending",
        )
        self.db.add(question)
        conversation.active_request = data.request_id
        conversation.busy_until = datetime.now(timezone.utc) + timedelta(seconds=LEASE_SECONDS)
        await self.db.commit()  # Save before the billable API call; release the DB connection.
        try:
            result = await generate(config, system, context)
        except asyncio.CancelledError:
            await asyncio.shield(self._finish(question, MentorResult(
                status="failed", answer=UNAVAILABLE, error_code="AI_REQUEST_CANCELLED",
            )))
            raise
        except Exception:
            result = MentorResult(status="failed", answer=UNAVAILABLE, error_code="AI_GENERATION_FAILED")
        return await self._finish(question, result)

    async def _finish(self, question, result):
        conversation = (await self.db.execute(select(AIConversation).where(
            AIConversation.conversation_id == question.conversation_id,
        ).with_for_update().execution_options(populate_existing=True))).scalar_one()
        if conversation.active_request != question.request_id:
            await self.db.rollback()
            raise HTTPException(409, detail={"code": "AI_REQUEST_EXPIRED", "message": "Request expired"})
        answer = AIAnswer(
            question_id=question.question_id, answer=result.answer, provider_response=result.raw,
            error_code=result.error_code, input_tokens=result.input_tokens, output_tokens=result.output_tokens,
        )
        self.db.add(answer)
        question.status = result.status
        if result.model is not None:
            question.model = result.model
        if result.status == "completed":
            conversation.summary = result.summary
            # Existing JSONB column now holds only local memory metadata, not remote session ids.
            conversation.provider_state = {"provider": "deepseek", "fingerprint": question.prompt_hash}
        conversation.active_request = None
        conversation.busy_until = None
        conversation.updated_at = datetime.now(timezone.utc)
        await self.db.commit()  # Ответ выдаётся только после сохранения аудита.
        if result.status == "failed":
            # Never log question text, API credentials, raw provider responses or exception strings.
            logger.warning("AI request failed question_id=%s model=%s code=%s",
                           question.question_id, question.model, result.error_code)
        return message(question, answer)
