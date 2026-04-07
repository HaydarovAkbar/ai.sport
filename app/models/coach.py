from datetime import datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.athlete import Athlete


class Coach(Base):
    __tablename__ = "coaches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    region: Mapped[str] = mapped_column(String(100), nullable=False)
    sport_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    experience_years: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    athletes: Mapped[List["Athlete"]] = relationship(back_populates="coach")

    def to_text(self) -> str:
        return (
            f"Trener: {self.full_name}. "
            f"Sport turi: {self.sport_type}. "
            f"Viloyat: {self.region}. "
            f"Tajriba: {self.experience_years} yil."
        )
