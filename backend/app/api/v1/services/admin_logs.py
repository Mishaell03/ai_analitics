from datetime import datetime, time, timezone

from sqlalchemy import func, literal, or_, select, union_all
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.admin_logs import AILogFilters, LogFilters, SystemLogFilters
from app.models.ai import AIAnswer, AIConversation, AIQuestion
from app.models.auth import UserSession
from app.models.errors import BackendErrorLog, UserEventLog
from app.models.users import User


class AdminLogsService:
    def __init__(self, db: AsyncSession):
        self.db = db

    @staticmethod
    def _filter_common(query, filters: LogFilters, created_at, user_id):
        # Границы календарных дат включительны, время хранения и фильтрации — UTC.
        if filters.date_from:
            query = query.where(created_at >= datetime.combine(filters.date_from, time.min, timezone.utc))
        if filters.date_to:
            query = query.where(created_at <= datetime.combine(filters.date_to, time.max, timezone.utc))
        if filters.user_id:
            query = query.where(user_id == filters.user_id)
        if filters.user and filters.user.strip():
            value = filters.user.strip()
            conditions = [User.name.icontains(value, autoescape=True), User.email.icontains(value, autoescape=True)]
            if value.isascii() and value.isdecimal() and int(value) <= 2147483647:
                conditions.append(user_id == int(value))
            query = query.where(or_(*conditions))
        return query

    async def _paginate(self, query, filters, *ordering):
        total = (await self.db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
        rows = await self.db.execute(
            query.order_by(*ordering).offset((filters.page - 1) * filters.page_size).limit(filters.page_size)
        )
        return {
            "page": filters.page,
            "page_size": filters.page_size,
            "total": total,
            "total_pages": max(1, (total + filters.page_size - 1) // filters.page_size),
            "items": [dict(row) for row in rows.mappings()],
        }

    async def get_system_logs(self, filters: SystemLogFilters):
        events = select(
            UserEventLog.id, literal("event").label("source"), UserEventLog.user_id,
            UserEventLog.session_id, UserEventLog.status_code, UserEventLog.event.label("code"),
            UserEventLog.request_method, UserEventLog.request_path, UserEventLog.created_at,
        )
        errors = select(
            BackendErrorLog.id, literal("backend").label("source"), UserSession.user_id,
            BackendErrorLog.session_id, BackendErrorLog.status_code, BackendErrorLog.error_code.label("code"),
            BackendErrorLog.request_method, BackendErrorLog.request_path, BackendErrorLog.created_at,
        ).outerjoin(UserSession, BackendErrorLog.session_id == UserSession.id)
        logs = union_all(events, errors).subquery()
        query = select(logs, User.name, User.email).outerjoin(User, User.user_id == logs.c.user_id)
        query = self._filter_common(query, filters, logs.c.created_at, logs.c.user_id)
        if filters.source:
            query = query.where(logs.c.source == filters.source)
        if filters.session_id:
            query = query.where(logs.c.session_id == filters.session_id)
        if filters.code:
            query = query.where(logs.c.code == filters.code.strip())
        if filters.status_code:
            query = query.where(logs.c.status_code == filters.status_code)
        if filters.status:
            lower, upper = {
                "success": (200, 299), "redirect": (300, 399),
                "client_error": (400, 499), "server_error": (500, 599),
            }[filters.status]
            query = query.where(logs.c.status_code.between(lower, upper))
        return await self._paginate(query, filters, logs.c.created_at.desc(), logs.c.source, logs.c.id.desc())

    async def get_ai_logs(self, filters: AILogFilters):
        # Не выдаём context_snapshot, provider_response, системный промпт и память модели.
        query = select(
            AIQuestion.question_id, AIQuestion.conversation_id, AIConversation.user_id,
            User.name, User.email, AIConversation.lesson_id, AIQuestion.question,
            AIAnswer.answer, AIQuestion.model, AIQuestion.status, AIAnswer.error_code, AIQuestion.created_at,
        ).join(AIConversation, AIQuestion.conversation_id == AIConversation.conversation_id).join(
            User, User.user_id == AIConversation.user_id,
        ).outerjoin(AIAnswer, AIAnswer.question_id == AIQuestion.question_id)
        query = self._filter_common(query, filters, AIQuestion.created_at, AIConversation.user_id)
        if filters.status:
            query = query.where(AIQuestion.status == filters.status)
        return await self._paginate(query, filters, AIQuestion.created_at.desc(), AIQuestion.question_id.desc())
