from pydantic import EmailStr, Field
from typing import Optional
from uuid import UUID

from app.schemas.base import AppBaseModel, TimestampMixin, IdMixin


class CandidateBase(AppBaseModel):
    full_name: str = Field(..., min_length=2, max_length=255, description="Candidate full name")
    phone: Optional[str] = Field(default=None, description="Phone number")
    education: Optional[str] = Field(default=None, description="Education background")
    experience_years: Optional[int] = Field(default=0, ge=0, description="Years of experience")
    skills: Optional[list[str]] = Field(default_factory=list, description="List of skills")
    resume_url: Optional[str] = Field(default=None, description="Resume file URL")
    linkedin_url: Optional[str] = Field(default=None, description="LinkedIn profile URL")
    portfolio_url: Optional[str] = Field(default=None, description="Portfolio website URL")


class CandidateCreate(CandidateBase):
    user_id: UUID = Field(..., description="Associated auth user ID")
    email: EmailStr = Field(..., description="Candidate email")


class CandidateUpdate(AppBaseModel):
    full_name: Optional[str] = Field(default=None, min_length=2, max_length=255)
    phone: Optional[str] = None
    education: Optional[str] = None
    experience_years: Optional[int] = Field(default=None, ge=0)
    skills: Optional[list[str]] = None
    resume_url: Optional[str] = None
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None


class CandidateResponse(CandidateBase, IdMixin, TimestampMixin):
    user_id: UUID
    email: EmailStr
    is_active: bool = Field(default=True)
    ats_score: Optional[float] = Field(default=None, description="ATS resume score (0-100)")
    resume_category: Optional[str] = Field(default=None, description="Resume classification category")
