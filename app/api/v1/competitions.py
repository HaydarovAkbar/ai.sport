from typing import Optional

from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DbDep, EmbDep
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.competition import CompetitionCreate, CompetitionRead, CompetitionUpdate
from app.services import competition_service

router = APIRouter(prefix="/competitions", tags=["competitions"])


@router.get("", response_model=PaginatedResponse[CompetitionRead])
async def list_competitions(
    db: DbDep,
    current_user: CurrentUser,
    sport_type: Optional[str] = None,
    year: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
):
    return await competition_service.list_competitions(db, sport_type, year, page, page_size)


@router.get("/{comp_id}", response_model=CompetitionRead)
async def get_competition(comp_id: int, db: DbDep, current_user: CurrentUser):
    return await competition_service.get_competition(db, comp_id)


@router.post("", response_model=CompetitionRead, status_code=201)
async def create_competition(body: CompetitionCreate, db: DbDep, admin: AdminUser, emb: EmbDep):
    return await competition_service.create_competition(db, body, emb)


@router.put("/{comp_id}", response_model=CompetitionRead)
async def update_competition(
    comp_id: int, body: CompetitionUpdate, db: DbDep, admin: AdminUser, emb: EmbDep
):
    return await competition_service.update_competition(db, comp_id, body, emb)


@router.delete("/{comp_id}", response_model=MessageResponse)
async def delete_competition(comp_id: int, db: DbDep, admin: AdminUser, emb: EmbDep):
    await competition_service.delete_competition(db, comp_id, emb)
    return MessageResponse(message="Musobaqa o'chirildi")
