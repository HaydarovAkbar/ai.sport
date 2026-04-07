from typing import Optional

from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DbDep, EmbDep
from app.schemas.coach import CoachCreate, CoachRead, CoachUpdate
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services import coach_service

router = APIRouter(prefix="/coaches", tags=["coaches"])


@router.get("", response_model=PaginatedResponse[CoachRead])
async def list_coaches(
    db: DbDep,
    current_user: CurrentUser,
    sport_type: Optional[str] = None,
    region: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
):
    return await coach_service.list_coaches(db, sport_type, region, page, page_size)


@router.get("/{coach_id}", response_model=CoachRead)
async def get_coach(coach_id: int, db: DbDep, current_user: CurrentUser):
    return await coach_service.get_coach(db, coach_id)


@router.post("", response_model=CoachRead, status_code=201)
async def create_coach(body: CoachCreate, db: DbDep, admin: AdminUser, emb: EmbDep):
    return await coach_service.create_coach(db, body, emb)


@router.put("/{coach_id}", response_model=CoachRead)
async def update_coach(coach_id: int, body: CoachUpdate, db: DbDep, admin: AdminUser, emb: EmbDep):
    return await coach_service.update_coach(db, coach_id, body, emb)


@router.delete("/{coach_id}", response_model=MessageResponse)
async def delete_coach(coach_id: int, db: DbDep, admin: AdminUser, emb: EmbDep):
    await coach_service.delete_coach(db, coach_id, emb)
    return MessageResponse(message="Trener o'chirildi")
