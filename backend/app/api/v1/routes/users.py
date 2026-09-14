from fastapi import APIRouter, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.session import CurrentUserContext, get_current_user
from app.core.database import get_db
from app.api.v1.schemas.users import MeResponse
from app.api.v1.services.users import user_service


router = APIRouter(prefix="/me")


@router.get("", response_model=MeResponse )
async def get_me(
    request: Request,
    current_user: CurrentUserContext = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await user_service.get_me(
        db=db,
        request=request,
        current_user=current_user,
    )