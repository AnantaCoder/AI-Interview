from pydantic import Field
from typing import Optional
from uuid import UUID

from app.schemas.base import AppBaseModel, TimestampMixin, IdMixin


class JobRoleBase(AppBaseModel):
    title: str = Field(..., min_length=2, max_length=255, description="Job role title")
    description: Optional[str] = Field(default=None, description="Job description")
    required_skills: list[str] = Field(default_factory=list, description="Required skills")
    preferred_skills: Optional[list[str]] = Field(default_factory=list, description="Preferred skills")
    min_experience_years: int = Field(default=0, ge=0, description="Minimum experience required")
    max_experience_years: Optional[int] = Field(default=None, ge=0, description="Maximum experience")
    education_requirement: Optional[str] = Field(default=None, description="Education requirements")
    salary_range_min: Optional[int] = Field(default=None, ge=0, description="Minimum salary")
    salary_range_max: Optional[int] = Field(default=None, ge=0, description="Maximum salary")
    location: Optional[str] = Field(default=None, description="Job location")
    is_remote: bool = Field(default=False, description="Is remote job")
    cutoff_score: float = Field(default=60.0, ge=0, le=100, description="Cutoff score for shortlisting")


class JobRoleCreate(JobRoleBase):
    organization_id: UUID = Field(..., description="Organization ID")


class JobRoleUpdate(AppBaseModel):
    title: Optional[str] = Field(default=None, min_length=2, max_length=255)
    description: Optional[str] = None
    required_skills: Optional[list[str]] = None
    preferred_skills: Optional[list[str]] = None
    min_experience_years: Optional[int] = Field(default=None, ge=0)
    max_experience_years: Optional[int] = Field(default=None, ge=0)
    education_requirement: Optional[str] = None
    salary_range_min: Optional[int] = Field(default=None, ge=0)
    salary_range_max: Optional[int] = Field(default=None, ge=0)
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    cutoff_score: Optional[float] = Field(default=None, ge=0, le=100)
    is_active: Optional[bool] = None


class JobRoleResponse(JobRoleBase, IdMixin, TimestampMixin):
    organization_id: UUID
    is_active: bool = Field(default=True)
    applicant_count: Optional[int] = Field(default=0, description="Number of applicants")
