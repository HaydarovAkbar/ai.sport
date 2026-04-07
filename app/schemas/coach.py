from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CoachCreate(BaseModel):
    full_name: str = Field(..., min_length=2, max_length=200)
    region: str = Field(..., min_length=2, max_length=100)
    sport_type: str = Field(..., min_length=2, max_length=100)
    experience_years: int = Field(..., ge=0, le=60)


class CoachUpdate(BaseModel):
    full_name: Optional[str] = Field(None, min_length=2, max_length=200)
    region: Optional[str] = Field(None, min_length=2, max_length=100)
    sport_type: Optional[str] = Field(None, min_length=2, max_length=100)
    experience_years: Optional[int] = Field(None, ge=0, le=60)


class CoachRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    full_name: str
    region: str
    sport_type: str
    experience_years: int
    created_at: datetime
