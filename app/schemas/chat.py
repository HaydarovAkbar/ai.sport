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
