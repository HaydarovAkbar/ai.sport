import json
import uuid
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ForbiddenException
from app.models.audit_log import AuditLog
from app.models.chat import ChatMessage, ChatSession
from app.schemas.chat import ChatResponse, JobStatusResponse, MessageRead, SessionRead
from app.schemas.common import PaginatedResponse
from app.services.rag_service import RAGService


class ChatService:
    def __init__(self, rag_service: RAGService) -> None:
        self.rag = rag_service

    async def send_message(
        self,
        db: AsyncSession,
        user_id: int,
        message: str,
        session_id: Optional[str],
        ip: Optional[str] = None,
    ) -> ChatResponse:
        # Get or create session
        session = await self._get_or_create_session(db, user_id, session_id)

        # Save user message
        user_msg = ChatMessage(session_id=session.id, role="user", content=message)
        db.add(user_msg)
        await db.flush()

        # Load history (exclude the just-added message)
        history_result = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session.id, ChatMessage.id != user_msg.id)
            .order_by(ChatMessage.created_at)
        )
        history = list(history_result.scalars().all())

        # RAG answer
        rag_result = await self.rag.answer(message, history, db)

        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=rag_result.answer,
            context_used=json.dumps(
                [{"type": c["type"], "id": c["id"], "text": c["text"]} for c in rag_result.chunks],
                ensure_ascii=False,
            ),
            tokens_used=rag_result.tokens_used,
        )
        db.add(assistant_msg)

        # Update session title if first exchange
        if not session.title:
            session.title = message[:80]

        # Audit log
        db.add(AuditLog(
            user_id=user_id,
            action="chat",
            resource="chat_session",
            resource_id=None,
            ip_address=ip,
            details=json.dumps(
                {"session_id": session.id, "tokens": rag_result.tokens_used},
                ensure_ascii=False,
            ),
        ))

        await db.flush()
        return ChatResponse(
            session_id=session.id,
            message_id=assistant_msg.id,
            answer=rag_result.answer,
            tokens_used=rag_result.tokens_used,
        )

    async def prepare_job(
        self,
        db: AsyncSession,
        user_id: int,
        message: str,
        session_id: Optional[str],
        ip: Optional[str] = None,
    ) -> tuple[str, int]:
        """
        Save user message to DB, return (session_id, user_msg_id).
        Called BEFORE enqueueing the ARQ job so the session always exists.
        """
        session = await self._get_or_create_session(db, user_id, session_id)

        user_msg = ChatMessage(session_id=session.id, role="user", content=message)
        db.add(user_msg)

        if not session.title:
            session.title = message[:80]

        await db.flush()
        return session.id, user_msg.id

    async def _get_or_create_session(
        self, db: AsyncSession, user_id: int, session_id: Optional[str]
    ) -> ChatSession:
        if session_id:
            result = await db.execute(
                select(ChatSession).where(ChatSession.id == session_id)
            )
            session = result.scalar_one_or_none()
            if not session:
                raise NotFoundException("Session topilmadi")
            if session.user_id != user_id:
                raise ForbiddenException()
            return session

        session = ChatSession(id=str(uuid.uuid4()), user_id=user_id)
        db.add(session)
        await db.flush()
        return session

    async def get_history(
        self, db: AsyncSession, session_id: str, user_id: int
    ) -> list[MessageRead]:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise NotFoundException("Session topilmadi")
        if session.user_id != user_id:
            raise ForbiddenException()

        msgs = await db.execute(
            select(ChatMessage)
            .where(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
        )
        return [MessageRead.model_validate(m) for m in msgs.scalars()]

    async def list_sessions(
        self, db: AsyncSession, user_id: int, page: int = 1, page_size: int = 20
    ) -> PaginatedResponse[SessionRead]:
        from sqlalchemy import func

        total_result = await db.execute(
            select(func.count()).where(ChatSession.user_id == user_id)
        )
        total = total_result.scalar_one()

        sessions_result = await db.execute(
            select(ChatSession)
            .where(ChatSession.user_id == user_id)
            .order_by(ChatSession.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        items = [SessionRead.model_validate(s) for s in sessions_result.scalars()]

        import math
        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if total else 0,
        )

    async def delete_session(
        self, db: AsyncSession, session_id: str, user_id: int
    ) -> None:
        result = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one_or_none()
        if not session:
            raise NotFoundException("Session topilmadi")
        if session.user_id != user_id:
            raise ForbiddenException()
        await db.delete(session)
