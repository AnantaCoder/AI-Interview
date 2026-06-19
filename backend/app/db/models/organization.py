from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.orm import relationship, Mapped, mapped_column

from app.db.models.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.user import User
    from app.db.models.job_role import JobRole


class Organization(BaseModel):
    __tablename__ = "organizations"
    
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    contact_email: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="organization")
    job_roles: Mapped[list["JobRole"]] = relationship("JobRole", back_populates="organization")
    
    def __repr__(self) -> str:
        return f"<Organization(id={self.id}, name={self.name})>"
