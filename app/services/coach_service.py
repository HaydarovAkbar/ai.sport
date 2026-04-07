import math
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.coach import Coach
from app.schemas.coach import CoachCreate, CoachRead, CoachUpdate
from app.schemas.common import PaginatedResponse
from app.services.embedding_service import EmbeddingService


async def list_coaches(
    db: AsyncSession,
    sport_type: Optional[str] = None,
    region: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[CoachRead]:
    q = select(Coach)
    if sport_type:
        q = q.where(Coach.sport_type.ilike(f"%{sport_type}%"))
    if region:
        q = q.where(Coach.region.ilike(f"%{region}%"))

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PaginatedResponse(
        items=[CoachRead.model_validate(c) for c in rows],
        total=total, page=page, page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def get_coach(db: AsyncSession, coach_id: int) -> Coach:
    result = await db.execute(select(Coach).where(Coach.id == coach_id))
    coach = result.scalar_one_or_none()
    if not coach:
        raise NotFoundException("Trener topilmadi")
    return coach


async def create_coach(
    db: AsyncSession, data: CoachCreate, emb: EmbeddingService
) -> Coach:
    coach = Coach(**data.model_dump())
    db.add(coach)
    await db.flush()
    await emb.add_record("coach", coach.id, coach.to_text())
    return coach


async def update_coach(
    db: AsyncSession, coach_id: int, data: CoachUpdate, emb: EmbeddingService
) -> Coach:
    coach = await get_coach(db, coach_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(coach, field, value)
    await db.flush()
    await emb.remove_record("coach", coach.id)
    await emb.add_record("coach", coach.id, coach.to_text())
    return coach


async def delete_coach(
    db: AsyncSession, coach_id: int, emb: EmbeddingService
) -> None:
    coach = await get_coach(db, coach_id)
    await emb.remove_record("coach", coach.id)
    await db.delete(coach)
