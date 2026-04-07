from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, DbDep, EmbDep
from app.core.rate_limiter import limiter
from app.schemas.chat import ChatRequest, ChatResponse, SessionRead
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.chat_service import ChatService
from app.services.rag_service import RAGService

router = APIRouter(prefix="/chat", tags=["chat"])


def _chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


@router.post("/message", response_model=ChatResponse)
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    body: ChatRequest,
    db: DbDep,
    current_user: CurrentUser,
) -> ChatResponse:
    svc = _chat_service(request)
    return await svc.send_message(
        db=db,
        user_id=current_user.id,
        message=body.message,
        session_id=body.session_id,
        ip=request.client.host if request.client else None,
    )


@router.get("/sessions", response_model=PaginatedResponse[SessionRead])
async def list_sessions(
    db: DbDep,
    current_user: CurrentUser,
    request: Request,
    page: int = 1,
    page_size: int = 20,
) -> PaginatedResponse[SessionRead]:
    svc = _chat_service(request)
    return await svc.list_sessions(db, current_user.id, page, page_size)


@router.get("/sessions/{session_id}/messages")
async def get_history(
    session_id: str,
    db: DbDep,
    current_user: CurrentUser,
    request: Request,
):
    svc = _chat_service(request)
    return await svc.get_history(db, session_id, current_user.id)


@router.delete("/sessions/{session_id}", response_model=MessageResponse)
async def delete_session(
    session_id: str,
    db: DbDep,
    current_user: CurrentUser,
    request: Request,
) -> MessageResponse:
    svc = _chat_service(request)
    await svc.delete_session(db, session_id, current_user.id)
    return MessageResponse(message="Session o'chirildi")
