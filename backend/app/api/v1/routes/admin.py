from datetime import date

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.admin import DashboardResponse
from app.api.v1.services.admin import AdminService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_admin
from app.core.users_events_logs import user_event_logs

router = APIRouter(prefix="/admin")


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
        request: Request,
        users: int | None = Query(default=None, description="Количество последних пользователей"),
        top_courses: int | None = Query(default=None, description="Количество курсов для аналитики"),
        # period: int | None = Query(default=None, description="Количество дней периода"),
        # date_of: date | None = Query(default=None, description="Начало периода"),
        # date_to: date | None = Query(default=None, description="Конец периода"),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    dashboard = await AdminService(db).get_dashboard(
        users=users,
        top_courses=top_courses,
        # period=period,
        # date_of=date_of,
        # date_to=date_to
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_DASHBOARD",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return dashboard
