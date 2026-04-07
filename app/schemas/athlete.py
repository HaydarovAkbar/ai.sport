from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.coach import CoachRead


class AthleteCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    birth_date: date
    region: str = Field(..., min_length=2, max_length=100)
    sport_type: str = Field(..., min_length=2, max_length=100)
    rank: Optional[str] = Field(None, max_length=100)
    coach_id: Optional[int] = None


class AthleteUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    birth_date: Optional[date] = None
    region: Optional[str] = Field(None, min_length=2, max_length=100)
    sport_type: Optional[str] = Field(None, min_length=2, max_length=100)
    rank: Optional[str] = Field(None, max_length=100)
    coach_id: Optional[int] = None


class AthleteRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    full_name: str
    birth_date: date
    region: str
    sport_type: str
    rank: Optional[str] = None
    coach_id: Optional[int] = None
    coach: Optional[CoachRead] = None
    created_at: datetime
