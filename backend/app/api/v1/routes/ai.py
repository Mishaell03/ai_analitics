from fastapi import APIRouter, Depends, Query, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.routes.student_exercises import CourseSlug, PositiveId
from app.api.v1.schemas.ai import AIHistoryResponse, AIMessageResponse, AIQuestionRequest
from app.api.v1.services.ai import LessonAIService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_user


def no_cache(response: Response):
    response.headers["Cache-Control"] = "no-store, private"


router = APIRouter(prefix="/courses", dependencies=[Depends(no_cache)])
AI_PATH = "/{course_slug}/modules/{module_id}/lessons/{lesson_id}/ai/messages"


@router.get(AI_PATH, response_model=AIHistoryResponse)
async def ai_history(
    course_slug: CourseSlug, module_id: PositiveId, lesson_id: PositiveId, request: Request,
    after_id: int = Query(default=0, ge=0), limit: int = Query(default=10, ge=1, le=10),
    db: AsyncSession = Depends(get_db), current: CurrentUserContext = Depends(get_current_user),
):
    return await LessonAIService(db).history(request, course_slug, module_id, lesson_id, current, after_id, limit)


@router.post(AI_PATH, response_model=AIMessageResponse)
async def ai_ask(
    course_slug: CourseSlug, module_id: PositiveId, lesson_id: PositiveId, request: Request,
    data: AIQuestionRequest, db: AsyncSession = Depends(get_db),
    current: CurrentUserContext = Depends(get_current_user),
):
    return await LessonAIService(db).ask(request, course_slug, module_id, lesson_id, current, data)
