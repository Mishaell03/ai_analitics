"""API УЧЕНИКА ДЛЯ ВЫПОЛНЕНИЯ PYTHON"""

from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.sandbox import SandboxExecuteResponse, SandboxExecuteRequest
from app.api.v1.services.sandbox import SandboxService
from app.core.database import get_db
from app.core.session import CurrentUserContext, get_current_user

router = APIRouter(prefix="/sandbox")


@router.post("/execute", response_model=SandboxExecuteResponse)
async def execute_sandbox(
        request: Request,
        data: SandboxExecuteRequest,
        db: AsyncSession = Depends(get_db),
        current: CurrentUserContext = Depends(get_current_user),
):
    result = await SandboxService(db).submit(request=request, data=data, current=current)
    return SandboxExecuteResponse(**result.execution.model_dump(), is_correct=result.is_correct)
