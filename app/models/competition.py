from datetime import date, datetime
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Date, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.result import Result


class Competition(Base):
    __tablename__ = "competitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    location: Mapped[str] = mapped_column(String(200), nullable=False)
    sport_type: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )

    results: Mapped[List["Result"]] = relationship(back_populates="competition")

    def to_text(self) -> str:
        return (
            f"Musobaqa: {self.name}. "
            f"Sana: {self.date}. "
            f"Joyi: {self.location}. "
            f"Sport turi: {self.sport_type}."
        )
