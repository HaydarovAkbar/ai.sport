from typing import Optional

from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DbDep, EmbDep
from app.schemas.athlete import AthleteCreate, AthleteRead, AthleteUpdate
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services import athlete_service

router = APIRouter(prefix="/athletes", tags=["athletes"])


@router.get("", response_model=PaginatedResponse[AthleteRead])
async def list_athletes(
    db: DbDep,
    current_user: CurrentUser,
    sport_type: Optional[str] = None,
    region: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    return await athlete_service.list_athletes(db, sport_type, region, page, page_size)


@router.get("/{athlete_id}", response_model=AthleteRead)
async def get_athlete(athlete_id: int, db: DbDep, current_user: CurrentUser):
    return await athlete_service.get_athlete(db, athlete_id)


@router.post("", response_model=AthleteRead, status_code=201)
async def create_athlete(body: AthleteCreate, db: DbDep, admin: AdminUser, emb: EmbDep):
    return await athlete_service.create_athlete(db, body, emb)


@router.put("/{athlete_id}", response_model=AthleteRead)
async def update_athlete(
    athlete_id: int, body: AthleteUpdate, db: DbDep, admin: AdminUser, emb: EmbDep
):
    return await athlete_service.update_athlete(db, athlete_id, body, emb)


@router.delete("/{athlete_id}", response_model=MessageResponse)
async def delete_athlete(athlete_id: int, db: DbDep, admin: AdminUser, emb: EmbDep):
    await athlete_service.delete_athlete(db, athlete_id, emb)
    return MessageResponse(message="Sportchi o'chirildi")
