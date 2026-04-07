from fastapi import APIRouter
from fastapi.requests import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select

from app.core.database import AsyncSessionLocal
from app.core.security import create_access_token, decode_token
from app.models.chat import ChatSession
from app.models.user import User

router = APIRouter(tags=["web-chat"])
templates = Jinja2Templates(directory="app/templates")


async def _get_user_from_cookie(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
    except Exception:
        return None
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()


@router.get("/", response_class=HTMLResponse)
async def root(request: Request):
    user = await _get_user_from_cookie(request)
    if not user:
        return RedirectResponse("/login")
    return RedirectResponse("/chat")


@router.get("/chat", response_class=HTMLResponse)
async def chat_page(request: Request, session_id: str = None):
    user = await _get_user_from_cookie(request)
    if not user:
        return RedirectResponse("/login")

    access_token = request.cookies.get("access_token", "")
    sessions = []
    messages = []

    async with AsyncSessionLocal() as db:
        sess_result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user.id)
            .order_by(ChatSession.created_at.desc())
            .limit(30)
        )
        sessions = list(sess_result.scalars().all())

        if session_id:
            from app.models.chat import ChatMessage
            msgs_result = await db.execute(
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at)
            )
            messages = list(msgs_result.scalars().all())

    return templates.TemplateResponse(
        "chat/index.html",
        {
            "request": request,
            "user": user,
            "sessions": sessions,
            "messages": messages,
            "session_id": session_id or "",
            "access_token": access_token,
            "active": "chat",
        },
    )
