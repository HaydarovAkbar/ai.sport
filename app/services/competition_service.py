import math
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException
from app.models.competition import Competition
from app.schemas.competition import CompetitionCreate, CompetitionRead, CompetitionUpdate
from app.schemas.common import PaginatedResponse
from app.services.embedding_service import EmbeddingService


async def list_competitions(
    db: AsyncSession,
    sport_type: Optional[str] = None,
    year: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[CompetitionRead]:
    q = select(Competition)
    if sport_type:
        q = q.where(Competition.sport_type.ilike(f"%{sport_type}%"))
    if year:
        from sqlalchemy import extract
        q = q.where(extract("year", Competition.date) == year)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PaginatedResponse(
        items=[CompetitionRead.model_validate(c) for c in rows],
        total=total, page=page, page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def get_competition(db: AsyncSession, comp_id: int) -> Competition:
    result = await db.execute(select(Competition).where(Competition.id == comp_id))
    comp = result.scalar_one_or_none()
    if not comp:
        raise NotFoundException("Musobaqa topilmadi")
    return comp


async def create_competition(
    db: AsyncSession, data: CompetitionCreate, emb: EmbeddingService
) -> Competition:
    comp = Competition(**data.model_dump())
    db.add(comp)
    await db.flush()
    await emb.add_record("competition", comp.id, comp.to_text())
    return comp


async def update_competition(
    db: AsyncSession, comp_id: int, data: CompetitionUpdate, emb: EmbeddingService
) -> Competition:
    comp = await get_competition(db, comp_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(comp, field, value)
    await db.flush()
    await emb.remove_record("competition", comp.id)
    await emb.add_record("competition", comp.id, comp.to_text())
    return comp


async def delete_competition(
    db: AsyncSession, comp_id: int, emb: EmbeddingService
) -> None:
    comp = await get_competition(db, comp_id)
    await emb.remove_record("competition", comp.id)
    await db.delete(comp)
