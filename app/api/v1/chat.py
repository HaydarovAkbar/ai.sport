from fastapi import APIRouter, Request

from app.api.deps import CurrentUser, DbDep
from app.core.exceptions import NotFoundException
from app.core.rate_limiter import limiter
from app.schemas.chat import (
    ChatRequest,
    JobStatusResponse,
    JobSubmittedResponse,
    SessionRead,
)
from app.schemas.common import MessageResponse, PaginatedResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["chat"])


def _chat_service(request: Request) -> ChatService:
    return request.app.state.chat_service


# ── Send message → enqueue ARQ job (202 Accepted) ─────────────────────

@router.post("/message", status_code=202, response_model=JobSubmittedResponse)
@limiter.limit("20/minute")
async def send_message(
    request: Request,
    body: ChatRequest,
    db: DbDep,
    current_user: CurrentUser,
) -> JobSubmittedResponse:
    """
    Enqueue chat message as background job.
    Returns {job_id, session_id} immediately (202 Accepted).
    Client polls GET /chat/jobs/{job_id} for the answer.
    """
    svc = _chat_service(request)

    # 1. Save user message & ensure session exists (sync DB step)
    session_id, user_msg_id = await svc.prepare_job(
        db=db,
        user_id=current_user.id,
        message=body.message,
        session_id=body.session_id,
        ip=request.client.host if request.client else None,
    )

    # 2. Enqueue background job via ARQ → Redis
    pool = request.app.state.arq_pool
    job = await pool.enqueue_job(
        "process_chat",
        current_user.id,
        session_id,
        user_msg_id,
        body.message,
        request.client.host if request.client else None,
    )

    return JobSubmittedResponse(job_id=job.job_id, session_id=session_id)


# ── Poll job status ────────────────────────────────────────────────────

@router.get("/jobs/{job_id}", response_model=JobStatusResponse)
async def get_job_status(
    job_id: str,
    request: Request,
    current_user: CurrentUser,
) -> JobStatusResponse:
    """
    Poll until status == 'complete' or 'failed'.
    Recommended polling interval: 1.5 seconds.
    """
    from arq.jobs import Job, JobStatus

    pool = request.app.state.arq_pool
    job = Job(job_id, pool)
    status = await job.status()

    if status == JobStatus.not_found:
        raise NotFoundException("Job topilmadi yoki muddati o'tgan")

    if status in (JobStatus.queued, JobStatus.deferred):
        return JobStatusResponse(job_id=job_id, status="queued")

    if status == JobStatus.in_progress:
        return JobStatusResponse(job_id=job_id, status="in_progress")

    # complete — may be success or exception
    try:
        result: dict = await job.result(timeout=2)
        return JobStatusResponse(job_id=job_id, status="complete", **result)
    except Exception as exc:
        return JobStatusResponse(job_id=job_id, status="failed", error=str(exc))


# ── Sessions & history ─────────────────────────────────────────────────

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
