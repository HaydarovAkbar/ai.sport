from typing import Optional

from fastapi import APIRouter

from app.api.deps import AdminUser, CurrentUser, DbDep, EmbDep
from app.schemas.common import MessageResponse, PaginatedResponse
from app.schemas.result import ResultCreate, ResultRead, ResultUpdate
from app.services import result_service

router = APIRouter(prefix="/results", tags=["results"])


@router.get("", response_model=PaginatedResponse[ResultRead])
async def list_results(
    db: DbDep,
    current_user: CurrentUser,
    athlete_id: Optional[int] = None,
    year: Optional[int] = None,
    place: Optional[int] = None,
    page: int = 1,
    page_size: int = 20,
):
    return await result_service.list_results(db, athlete_id, year, place, page, page_size)


@router.get("/{result_id}", response_model=ResultRead)
async def get_result(result_id: int, db: DbDep, current_user: CurrentUser):
    return await result_service._load(db, result_id)


@router.post("", response_model=ResultRead, status_code=201)
async def create_result(body: ResultCreate, db: DbDep, admin: AdminUser, emb: EmbDep):
    return await result_service.create_result(db, body, emb)


@router.put("/{result_id}", response_model=ResultRead)
async def update_result(
    result_id: int, body: ResultUpdate, db: DbDep, admin: AdminUser, emb: EmbDep
):
    return await result_service.update_result(db, result_id, body, emb)


@router.delete("/{result_id}", response_model=MessageResponse)
async def delete_result(result_id: int, db: DbDep, admin: AdminUser, emb: EmbDep):
    await result_service.delete_result(db, result_id, emb)
    return MessageResponse(message="Natija o'chirildi")
