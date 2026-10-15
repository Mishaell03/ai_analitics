from datetime import date

from fastapi import APIRouter, Depends, Request, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.admin import (
    AdminQuantityUsers,
    AdminUserDetail,
    DashboardResponse,
)
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


@router.get("/users", response_model=AdminQuantityUsers)
async def get_users(
        request: Request,
        page: int = Query(default=1, ge=1, description="Номер страницы"),
        per_page: int = Query(default=10, ge=1, le=100, description="Пользователей на странице"),
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    users = await AdminService(db).get_users(
        page=page,
        per_page=per_page,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_USERS",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return users


@router.get("/users/{user_id}", response_model=AdminUserDetail)
async def get_user_detail(
        request: Request,
        user_id: int,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    detail = await AdminService(db).get_user_detail(
        request=request,
        user_id=user_id,
        language=current.session.language,
        device_id=current.session.device_id,
        session_id=current.session.id,
        admin_id=current.session.user_id,
        platform=current.session.platform,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_GET_ADMIN_USER_DETAIL",
        status_code=200,
        device_id=current.session.device_id,
        user_id=current.session.user_id,
        session_id=current.session.id,
        platform=current.session.platform,
    )

    return detail