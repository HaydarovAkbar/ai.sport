import math
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.athlete import Athlete
from app.schemas.athlete import AthleteCreate, AthleteRead, AthleteUpdate
from app.schemas.common import PaginatedResponse
from app.services.embedding_service import EmbeddingService


async def list_athletes(
    db: AsyncSession,
    sport_type: Optional[str] = None,
    region: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[AthleteRead]:
    q = select(Athlete).options(selectinload(Athlete.coach))
    if sport_type:
        q = q.where(Athlete.sport_type.ilike(f"%{sport_type}%"))
    if region:
        q = q.where(Athlete.region.ilike(f"%{region}%"))

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PaginatedResponse(
        items=[AthleteRead.model_validate(a) for a in rows],
        total=total, page=page, page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def get_athlete(db: AsyncSession, athlete_id: int) -> Athlete:
    result = await db.execute(
        select(Athlete).options(selectinload(Athlete.coach)).where(Athlete.id == athlete_id)
    )
    athlete = result.scalar_one_or_none()
    if not athlete:
        raise NotFoundException("Sportchi topilmadi")
    return athlete


async def create_athlete(
    db: AsyncSession, data: AthleteCreate, emb: EmbeddingService
) -> Athlete:
    athlete = Athlete(**data.model_dump())
    db.add(athlete)
    await db.flush()
    # Reload with coach relationship for to_text()
    athlete = await get_athlete(db, athlete.id)
    await emb.add_record("athlete", athlete.id, athlete.to_text())
    return athlete


async def update_athlete(
    db: AsyncSession, athlete_id: int, data: AthleteUpdate, emb: EmbeddingService
) -> Athlete:
    athlete = await get_athlete(db, athlete_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(athlete, field, value)
    await db.flush()
    athlete = await get_athlete(db, athlete.id)
    await emb.remove_record("athlete", athlete.id)
    await emb.add_record("athlete", athlete.id, athlete.to_text())
    return athlete


async def delete_athlete(
    db: AsyncSession, athlete_id: int, emb: EmbeddingService
) -> None:
    athlete = await get_athlete(db, athlete_id)
    await emb.remove_record("athlete", athlete.id)
    await db.delete(athlete)
