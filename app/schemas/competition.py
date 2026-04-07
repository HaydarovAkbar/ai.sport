from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class CompetitionCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=300)
    date: date
    location: str = Field(..., min_length=2, max_length=200)
    sport_type: str = Field(..., min_length=2, max_length=100)


class CompetitionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=300)
    date: Optional[date] = None
    location: Optional[str] = Field(None, min_length=2, max_length=200)
    sport_type: Optional[str] = Field(None, min_length=2, max_length=100)


class CompetitionRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    date: date
    location: str
    sport_type: str
    created_at: datetime
