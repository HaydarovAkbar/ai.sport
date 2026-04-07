from typing import Optional

from fastapi import APIRouter, Request

from app.api.deps import AdminUser, DbDep, EmbDep
from app.schemas.common import MessageResponse
from app.schemas.user import UserCreate, UserRead, UserUpdate
from app.services import admin_service
from app.services.auth_service import create_user
from app.services.embedding_service import EmbeddingService

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats")
async def stats(db: DbDep, admin: AdminUser, emb: EmbDep):
    return await admin_service.get_stats(db, emb)


@router.post("/index/rebuild", response_model=MessageResponse)
async def rebuild_index(request: Request, db: DbDep, admin: AdminUser):
    emb: EmbeddingService = request.app.state.embedding_service
    await emb.build_full_index(db)
    return MessageResponse(message=f"Index qayta qurildi. Hujjatlar: {emb.doc_count}")


@router.get("/index/status")
async def index_status(request: Request, admin: AdminUser):
    emb: EmbeddingService = request.app.state.embedding_service
    return {"doc_count": emb.doc_count}


@router.get("/audit-logs")
async def audit_logs(
    db: DbDep,
    admin: AdminUser,
    action: Optional[str] = None,
    user_id: Optional[int] = None,
    page: int = 1,
    page_size: int = 50,
):
    return await admin_service.get_audit_logs(db, action, user_id, page, page_size)


@router.post("/users", response_model=UserRead, status_code=201)
async def create_new_user(body: UserCreate, db: DbDep, admin: AdminUser):
    user = await create_user(db, body)
    return UserRead.model_validate(user)
