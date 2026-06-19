from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Text, Integer, Boolean, Float, ForeignKey, JSON
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.models.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.organization import Organization
    from app.db.models.interview import Interview, InterviewQuestion


class JobRole(BaseModel):
    __tablename__ = "job_roles"
    
    organization_id: Mapped[str] = mapped_column(String(36), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    required_skills: Mapped[list[str]] = mapped_column(JSON, default=[])
    preferred_skills: Mapped[list[str]] = mapped_column(JSON, default=[])
    min_experience_years: Mapped[int] = mapped_column(Integer, default=0)
    max_experience_years: Mapped[int | None] = mapped_column(Integer, nullable=True)
    education_requirement: Mapped[str | None] = mapped_column(String(255), nullable=True)
    salary_range_min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    salary_range_max: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_remote: Mapped[bool] = mapped_column(Boolean, default=False)
    cutoff_score: Mapped[float] = mapped_column(Float, default=60.0)
    
    # Relationships
    organization: Mapped["Organization"] = relationship("Organization", back_populates="job_roles")
    interviews: Mapped[list["Interview"]] = relationship("Interview", back_populates="job_role")
    questions: Mapped[list["InterviewQuestion"]] = relationship("InterviewQuestion", back_populates="job_role")
    
    def __repr__(self) -> str:
        return f"<JobRole(id={self.id}, title={self.title})>"
