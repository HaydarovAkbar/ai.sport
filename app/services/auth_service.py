import json
from datetime import UTC, datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ConflictException, CredentialsException, NotFoundException
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.models.audit_log import AuditLog
from app.models.user import User, UserRole
from app.schemas.user import UserCreate


async def authenticate_user(
    db: AsyncSession, username: str, password: str, ip: Optional[str] = None
) -> tuple[User, str, str]:
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()

    if not user or not verify_password(password, user.hashed_password):
        await _log(db, None, "login_failed", ip=ip, details={"username": username})
        raise CredentialsException("Username yoki parol noto'g'ri")

    if not user.is_active:
        raise CredentialsException("Foydalanuvchi bloklangan")

    user.last_login = datetime.now(UTC)

    access_token = create_access_token(user.id, user.role.value)
    refresh_token = create_refresh_token(user.id)

    await _log(db, user.id, "login", ip=ip)
    return user, access_token, refresh_token


async def refresh_access(db: AsyncSession, refresh_token: str) -> str:
    payload = decode_token(refresh_token)
    if payload.get("type") != "refresh":
        raise CredentialsException("Noto'g'ri token turi")

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise CredentialsException("Foydalanuvchi topilmadi yoki bloklangan")

    return create_access_token(user.id, user.role.value)


async def get_user_from_token(db: AsyncSession, token: str) -> User:
    payload = decode_token(token)
    if payload.get("type") != "access":
        raise CredentialsException("Noto'g'ri token turi")

    user_id = int(payload["sub"])
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise CredentialsException("Foydalanuvchi topilmadi")

    return user


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    existing = await db.execute(
        select(User).where(
            (User.username == data.username) | (User.email == data.email)
        )
    )
    if existing.scalar_one_or_none():
        raise ConflictException("Bu username yoki email band")

    user = User(
        username=data.username,
        email=data.email,
        hashed_password=hash_password(data.password),
        role=data.role,
    )
    db.add(user)
    await db.flush()
    return user


async def _log(
    db: AsyncSession,
    user_id: Optional[int],
    action: str,
    ip: Optional[str] = None,
    details: Optional[dict] = None,
) -> None:
    log = AuditLog(
        user_id=user_id,
        action=action,
        ip_address=ip,
        details=json.dumps(details, ensure_ascii=False) if details else None,
    )
    db.add(log)
