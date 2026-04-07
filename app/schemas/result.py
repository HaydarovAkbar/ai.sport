from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.schemas.athlete import AthleteRead
from app.schemas.competition import CompetitionRead


class ResultCreate(BaseModel):
    athlete_id: int
    competition_id: int
    place: Optional[int] = Field(None, ge=1)
    score: Optional[float] = Field(None, ge=0)
    year: int = Field(..., ge=1990, le=2100)


class ResultUpdate(BaseModel):
    place: Optional[int] = Field(None, ge=1)
    score: Optional[float] = Field(None, ge=0)
    year: Optional[int] = Field(None, ge=1990, le=2100)


class ResultRead(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    athlete_id: int
    competition_id: int
    place: Optional[int] = None
    score: Optional[float] = None
    year: int
    athlete: Optional[AthleteRead] = None
    competition: Optional[CompetitionRead] = None
    created_at: datetime
