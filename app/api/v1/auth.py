from fastapi import APIRouter, Request, Response
from fastapi.security import OAuth2PasswordRequestForm
from typing import Annotated
from fastapi import Depends

from app.api.deps import CurrentUser, DbDep
from app.core.rate_limiter import limiter
from app.schemas.auth import TokenResponse
from app.schemas.user import UserRead
from app.services.auth_service import authenticate_user, refresh_access

router = APIRouter(prefix="/auth", tags=["auth"])

REFRESH_COOKIE = "refresh_token"


@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
async def login(
    request: Request,
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbDep,
) -> TokenResponse:
    user, access_token, refresh_token = await authenticate_user(
        db, form_data.username, form_data.password, ip=request.client.host if request.client else None
    )
    response.set_cookie(
        REFRESH_COOKIE, refresh_token, httponly=True, samesite="lax", max_age=7 * 24 * 3600
    )
    return TokenResponse(access_token=access_token)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(request: Request, db: DbDep) -> TokenResponse:
    token = request.cookies.get(REFRESH_COOKIE)
    if not token:
        from app.core.exceptions import CredentialsException
        raise CredentialsException("Refresh token yo'q")
    access_token = await refresh_access(db, token)
    return TokenResponse(access_token=access_token)


@router.post("/logout")
async def logout(response: Response) -> dict:
    response.delete_cookie(REFRESH_COOKIE)
    return {"message": "Chiqildi"}


@router.get("/me", response_model=UserRead)
async def me(current_user: CurrentUser) -> UserRead:
    return UserRead.model_validate(current_user)
