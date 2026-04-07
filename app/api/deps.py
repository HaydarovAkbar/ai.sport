from typing import Annotated

from fastapi import Depends, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenException
from app.models.user import User, UserRole
from app.services.auth_service import get_user_from_token
from app.services.embedding_service import EmbeddingService

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DbDep = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user(token: TokenDep, db: DbDep) -> User:
    return await get_user_from_token(db, token)


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != UserRole.ADMIN:
        raise ForbiddenException("Admin huquqi talab qilinadi")
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]


def get_embedding_service(request: Request) -> EmbeddingService:
    return request.app.state.embedding_service


EmbDep = Annotated[EmbeddingService, Depends(get_embedding_service)]
