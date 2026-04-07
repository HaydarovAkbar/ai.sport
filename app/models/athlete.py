from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.coach import Coach
    from app.models.result import Result


class Athlete(Base):
    __tablename__ = "athletes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=False, index=True)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    region: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    sport_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    rank: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    coach_id: Mapped[Optional[int]] = mapped_column(
        Integer, ForeignKey("coaches.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), onupdate=func.now(), nullable=True
    )

    coach: Mapped[Optional["Coach"]] = relationship(back_populates="athletes")
    results: Mapped[List["Result"]] = relationship(back_populates="athlete")

    def to_text(self) -> str:
        coach_name = self.coach.full_name if self.coach else "yo'q"
        return (
            f"Sportchi: {self.full_name}. "
            f"Tug'ilgan sana: {self.birth_date}. "
            f"Viloyat: {self.region}. "
            f"Sport turi: {self.sport_type}. "
            f"Daraja: {self.rank or 'belgilanmagan'}. "
            f"Trener: {coach_name}."
        )
