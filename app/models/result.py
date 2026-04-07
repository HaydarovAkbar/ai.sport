from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.athlete import Athlete
    from app.models.competition import Competition


class Result(Base):
    __tablename__ = "results"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    athlete_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("athletes.id", ondelete="CASCADE"), nullable=False, index=True
    )
    competition_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("competitions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    place: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    year: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    athlete: Mapped["Athlete"] = relationship(back_populates="results")
    competition: Mapped["Competition"] = relationship(back_populates="results")

    def to_text(self) -> str:
        place_str = f"{self.place}-o'rin" if self.place else "o'rin belgilanmagan"
        score_str = str(self.score) if self.score else "ko'rsatilmagan"
        return (
            f"Natija: {self.athlete.full_name} sportchi "
            f"{self.competition.name} musobaqasida {place_str} oldi. "
            f"Yil: {self.year}. Ball: {score_str}."
        )
