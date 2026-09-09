from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import BaseRegisterResponse, BaseRegisterRequest
from app.api.v1.services.auth import BaseAuthService
from app.core.database import get_db

router = APIRouter()

@router.post("/register", response_model=BaseRegisterResponse)
async def register_user(
        data: BaseRegisterRequest,
        request: Request,
        db: AsyncSession = Depends(get_db)
):
    session = await BaseAuthService(db).register(
        data=data,
        request=request,
    )

    return BaseRegisterResponse(
        session=session,
    )