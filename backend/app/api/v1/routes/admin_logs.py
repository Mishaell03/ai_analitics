from typing import Annotated

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.admin_logs import AILogFilters, AILogsResponse, SystemLogFilters, SystemLogsResponse
from app.api.v1.services.admin_logs import AdminLogsService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_admin

router = APIRouter(prefix="/admin/logs")


@router.get("", response_model=SystemLogsResponse)
async def get_system_logs(
        response: Response,
        filters: Annotated[SystemLogFilters, Query()],
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    response.headers["Cache-Control"] = "no-store"
    return await AdminLogsService(db).get_system_logs(filters)


@router.get("/ai", response_model=AILogsResponse)
async def get_ai_logs(
        response: Response,
        filters: Annotated[AILogFilters, Query()],
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_admin),
):
    response.headers["Cache-Control"] = "no-store"
    return await AdminLogsService(db).get_ai_logs(filters)
