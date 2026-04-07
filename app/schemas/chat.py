from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=1000)
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    session_id: str
    message_id: int
    answer: str
    tokens_used: Optional[int] = None


# ── Job-based chat schemas ─────────────────────────────────────────────

class JobSubmittedResponse(BaseModel):
    """Returned immediately when message is enqueued (HTTP 202)."""
    job_id: str
    session_id: str
    status: str = "queued"


class JobStatusResponse(BaseModel):
    """Returned when polling job status."""
    job_id: str
    status: str          # queued | in_progress | complete | failed | not_found
    session_id: Optional[str] = None
    message_id: Optional[int] = None
    answer: Optional[str] = None
    tokens_used: Optional[int] = None
    error: Optional[str] = None


class MessageRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    role: str
    content: str
    tokens_used: Optional[int] = None
    created_at: datetime


class SessionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    title: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None


class SessionWithMessages(SessionRead):
    messages: List[MessageRead] = []
