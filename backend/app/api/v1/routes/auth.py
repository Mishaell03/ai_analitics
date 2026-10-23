from fastapi import APIRouter, Request, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.schemas.auth import BaseAuthResponse, BaseAuthRequest, RegisterRequest
from app.api.v1.services.auth import BaseAuthService
from app.core.config import settings
from app.core.database import get_db
from app.core.rate_limit import login_rate_limit, register_rate_limit
from app.core.session import revoke_session
from app.core.users_events_logs import user_event_logs

router = APIRouter()

SESSION_COOKIE_NAME = "session_token"


def _set_session_cookie(response: Response, token: str) -> None:
    response.set_cookie(
        key=SESSION_COOKIE_NAME,
        value=token,
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
        path="/",
        max_age=settings.session_ttl_days * 24 * 60 * 60,
    )


def _clear_session_cookie(response: Response) -> None:
    response.delete_cookie(
        key=SESSION_COOKIE_NAME,
        path="/",
        httponly=True,
        secure=settings.session_cookie_secure,
        samesite=settings.session_cookie_samesite,
    )


@router.post(
    "/register",
    response_model=BaseAuthResponse,
    dependencies=[Depends(register_rate_limit)],
)
async def register_user(
        data: RegisterRequest,
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db)
):
    session = await BaseAuthService(db).register(
        data=data,
        request=request,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_USERS_REGISTRATION",
        status_code=200,
        device_id=session.device_id,
        user_id=session.user_id,
        session_id=session.session_id,
    )

    _set_session_cookie(response=response, token=session.session)

    return BaseAuthResponse(
        success=True,
    )


@router.post(
    "/auth",
    response_model=BaseAuthResponse,
    dependencies=[Depends(login_rate_limit)],
)
async def auth_user(
        data: BaseAuthRequest,
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db)
):
    session = await BaseAuthService(db).auth(
        data=data,
        request=request,
    )

    await user_event_logs(
        request=request,
        event="SUCCESS_USERS_AUTH",
        status_code=200,
        device_id=session.device_id,
        user_id=session.user_id,
        session_id=session.session_id,
    )

    _set_session_cookie(response=response, token=session.session)

    return BaseAuthResponse(
        success=True,
    )


@router.post("/logout", response_model=BaseAuthResponse)
async def logout_user(
        request: Request,
        response: Response,
        db: AsyncSession = Depends(get_db),
):
    """Отзывает текущую сессию и удаляет cookie.

    Идемпотентен: без активной сессии всё равно возвращает success.
    """

    session_token = request.cookies.get(SESSION_COOKIE_NAME)

    if session_token:
        await revoke_session(db=db, session_token=session_token)

    await user_event_logs(
        request=request,
        event="SUCCESS_USERS_LOGOUT",
        status_code=200,
    )

    _clear_session_cookie(response=response)

    return BaseAuthResponse(
        success=True,
    )
