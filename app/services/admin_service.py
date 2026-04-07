from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.athlete import Athlete
from app.models.audit_log import AuditLog
from app.models.chat import ChatSession
from app.models.coach import Coach
from app.models.competition import Competition
from app.models.result import Result
from app.models.user import User
from app.services.embedding_service import EmbeddingService


async def get_stats(db: AsyncSession, emb: EmbeddingService) -> dict:
    athletes = (await db.execute(select(func.count()).select_from(Athlete))).scalar_one()
    coaches = (await db.execute(select(func.count()).select_from(Coach))).scalar_one()
    competitions = (await db.execute(select(func.count()).select_from(Competition))).scalar_one()
    results = (await db.execute(select(func.count()).select_from(Result))).scalar_one()
    users = (await db.execute(select(func.count()).select_from(User))).scalar_one()
    sessions = (await db.execute(select(func.count()).select_from(ChatSession))).scalar_one()

    recent_logs = (
        await db.execute(
            select(AuditLog).order_by(AuditLog.created_at.desc()).limit(10)
        )
    ).scalars().all()

    return {
        "counts": {
            "athletes": athletes,
            "coaches": coaches,
            "competitions": competitions,
            "results": results,
            "users": users,
            "sessions": sessions,
            "faiss_docs": emb.doc_count,
        },
        "recent_logs": [
            {
                "id": log.id,
                "action": log.action,
                "user_id": log.user_id,
                "ip_address": log.ip_address,
                "created_at": log.created_at.isoformat(),
            }
            for log in recent_logs
        ],
    }


async def get_audit_logs(
    db: AsyncSession,
    action: str | None = None,
    user_id: int | None = None,
    page: int = 1,
    page_size: int = 50,
) -> dict:
    import math

    q = select(AuditLog).order_by(AuditLog.created_at.desc())
    if action:
        q = q.where(AuditLog.action == action)
    if user_id:
        q = q.where(AuditLog.user_id == user_id)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()

    return {
        "items": [
            {
                "id": log.id,
                "action": log.action,
                "user_id": log.user_id,
                "resource": log.resource,
                "ip_address": log.ip_address,
                "details": log.details,
                "created_at": log.created_at.isoformat(),
            }
            for log in rows
        ],
        "total": total,
        "page": page,
        "pages": math.ceil(total / page_size) if total else 0,
    }
