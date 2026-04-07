"""
ARQ Chat Worker
Runs in a separate process. Each chat message is processed as a background job.

Start with:
    arq app.workers.chat_worker.WorkerSettings
"""
import json
from typing import Optional

from arq.connections import RedisSettings
from openai import AsyncOpenAI
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.core.config import settings
from app.core.logging_config import logger
from app.models.audit_log import AuditLog
from app.models.chat import ChatMessage


async def process_chat(
    ctx: dict,
    user_id: int,
    session_id: str,
    user_msg_id: int,
    message: str,
    ip: Optional[str] = None,
) -> dict:
    """
    Background job: run RAG pipeline and save assistant reply.
    Returns dict with {session_id, message_id, answer, tokens_used}.
    """
    rag_service = ctx["rag_service"]
    db_factory = ctx["db_factory"]

    async with db_factory() as db:
        # Load chat history (all messages except the current user message)
        history_result = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.id != user_msg_id,
            )
            .order_by(ChatMessage.created_at)
        )
        history = list(history_result.scalars().all())

        # Run RAG pipeline
        rag_result = await rag_service.answer(message, history, db)

        # Save assistant message
        assistant_msg = ChatMessage(
            session_id=session_id,
            role="assistant",
            content=rag_result.answer,
            context_used=json.dumps(
                [{"type": c["type"], "id": c["id"], "text": c["text"]} for c in rag_result.chunks],
                ensure_ascii=False,
            ),
            tokens_used=rag_result.tokens_used,
        )
        db.add(assistant_msg)

        # Audit log
        db.add(AuditLog(
            user_id=user_id,
            action="chat",
            ip_address=ip,
            details=json.dumps(
                {"session_id": session_id, "tokens": rag_result.tokens_used},
                ensure_ascii=False,
            ),
        ))

        await db.commit()
        await db.refresh(assistant_msg)

    logger.info(
        "job_chat_done",
        session_id=session_id,
        tokens=rag_result.tokens_used,
        user_id=user_id,
    )

    return {
        "session_id": session_id,
        "message_id": assistant_msg.id,
        "answer": rag_result.answer,
        "tokens_used": rag_result.tokens_used,
    }


# ── Worker lifecycle ───────────────────────────────────────────────────

async def startup(ctx: dict) -> None:
    """Initialize all services for the worker process."""
    from app.services.embedding_service import EmbeddingService
    from app.services.rag_service import RAGService

    openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    engine = create_async_engine(settings.ASYNC_DATABASE_URL, echo=False)
    db_factory = async_sessionmaker(engine, expire_on_commit=False)

    embedding_service = EmbeddingService(openai_client)
    async with db_factory() as db:
        await embedding_service.initialize(db)

    rag_service = RAGService(embedding_service, openai_client)

    ctx["engine"] = engine
    ctx["db_factory"] = db_factory
    ctx["rag_service"] = rag_service
    ctx["embedding_service"] = embedding_service

    logger.info("worker_started", faiss_docs=embedding_service.doc_count)


async def shutdown(ctx: dict) -> None:
    await ctx["engine"].dispose()
    logger.info("worker_stopped")


# ── Worker settings ────────────────────────────────────────────────────

class WorkerSettings:
    functions = [process_chat]
    on_startup = startup
    on_shutdown = shutdown
    redis_settings = RedisSettings(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        database=settings.REDIS_DB,
        password=settings.REDIS_PASSWORD or None,
    )
    max_jobs = 10
    job_timeout = 120           # seconds — max time for one job
    keep_result = 3600          # seconds — keep result in Redis for 1 hour
    keep_result_forever = False
    retry_jobs = True
    max_tries = 2
