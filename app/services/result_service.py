import math
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.exceptions import NotFoundException
from app.models.result import Result
from app.schemas.common import PaginatedResponse
from app.schemas.result import ResultCreate, ResultRead, ResultUpdate
from app.services.embedding_service import EmbeddingService


async def _load(db: AsyncSession, result_id: int) -> Result:
    row = (
        await db.execute(
            select(Result)
            .options(selectinload(Result.athlete), selectinload(Result.competition))
            .where(Result.id == result_id)
        )
    ).scalar_one_or_none()
    if not row:
        raise NotFoundException("Natija topilmadi")
    return row


async def list_results(
    db: AsyncSession,
    athlete_id: Optional[int] = None,
    year: Optional[int] = None,
    place: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[ResultRead]:
    q = select(Result).options(selectinload(Result.athlete), selectinload(Result.competition))
    if athlete_id:
        q = q.where(Result.athlete_id == athlete_id)
    if year:
        q = q.where(Result.year == year)
    if place:
        q = q.where(Result.place == place)

    total = (await db.execute(select(func.count()).select_from(q.subquery()))).scalar_one()
    rows = (await db.execute(q.offset((page - 1) * page_size).limit(page_size))).scalars().all()
    return PaginatedResponse(
        items=[ResultRead.model_validate(r) for r in rows],
        total=total, page=page, page_size=page_size,
        pages=math.ceil(total / page_size) if total else 0,
    )


async def create_result(
    db: AsyncSession, data: ResultCreate, emb: EmbeddingService
) -> Result:
    result = Result(**data.model_dump())
    db.add(result)
    await db.flush()
    row = await _load(db, result.id)
    await emb.add_record("result", row.id, row.to_text())
    return row


async def update_result(
    db: AsyncSession, result_id: int, data: ResultUpdate, emb: EmbeddingService
) -> Result:
    row = await _load(db, result_id)
    for field, value in data.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    await db.flush()
    row = await _load(db, result_id)
    await emb.remove_record("result", row.id)
    await emb.add_record("result", row.id, row.to_text())
    return row


async def delete_result(
    db: AsyncSession, result_id: int, emb: EmbeddingService
) -> None:
    row = await _load(db, result_id)
    await emb.remove_record("result", row.id)
    await db.delete(row)
