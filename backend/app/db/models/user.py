from __future__ import annotations

from typing import TYPE_CHECKING

from sqlalchemy import Column, String, Boolean, JSON, Integer
from sqlalchemy.orm import relationship, Mapped, mapped_column
import enum

from app.db.models.base import BaseModel

if TYPE_CHECKING:
    from app.db.models.organization import Organization
    from app.db.models.candidate import Candidate


class UserType(str, enum.Enum):
    ORGANIZATION = "organization"
    CANDIDATE = "candidate"
    ADMIN = "admin"


class User(BaseModel):
    __tablename__ = "users"
    
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)  # Nullable for OAuth users
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    user_type: Mapped[str] = mapped_column(String(20), nullable=False)
    
    # Profile Extensions
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    skills: Mapped[list[str]] = mapped_column(JSON, default=[])
    job_role: Mapped[str | None] = mapped_column(String(255), nullable=True)
    year_of_experience: Mapped[int] = mapped_column(Integer, default=0)
    
    # OAuth fields
    provider: Mapped[str | None] = mapped_column(String(50), nullable=True)  # google, email, etc.
    provider_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    
    # Email verification
    email_verified: Mapped[str] = mapped_column(String(1), default="N")
    
    # Relationships
    organization: Mapped["Organization | None"] = relationship("Organization", back_populates="user", uselist=False)
    candidate: Mapped["Candidate | None"] = relationship("Candidate", back_populates="user", uselist=False)
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email}, type={self.user_type})>"
