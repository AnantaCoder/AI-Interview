from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Text, Integer, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.models.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.interview import Interview


class Candidate(BaseModel):
    __tablename__ = "candidates"
    
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    education: Mapped[str | None] = mapped_column(Text, nullable=True)
    experience_years: Mapped[int] = mapped_column(Integer, default=0)
    skills: Mapped[list[str]] = mapped_column(JSON, default=[])
    resume_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    linkedin_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    portfolio_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    
    # ATS scoring
    ats_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    resume_category: Mapped[str | None] = mapped_column(String(100), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="candidate")
    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="candidate")
    
    def __repr__(self) -> str:
        return f"<Candidate(id={self.id}, name={self.full_name})>"
