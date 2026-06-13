from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
from app.schemas.candidate import CandidateResponse
class CampaignBase(BaseModel):
    title: str
    description: Optional[str] = None
    required_skills: Optional[List[str]] = []
    preferred_skills: Optional[List[str]] = []
    min_experience_years: Optional[int] = 0
    max_experience_years: Optional[int] = None
    education_requirement: Optional[str] = None
    salary_range_min: Optional[int] = None
    salary_range_max: Optional[int] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = False
    cutoff_score: Optional[float] = 60.0

class CampaignCreate(CampaignBase):
    pass

class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    required_skills: Optional[List[str]] = None
    preferred_skills: Optional[List[str]] = None
    min_experience_years: Optional[int] = None
    max_experience_years: Optional[int] = None
    education_requirement: Optional[str] = None
    salary_range_min: Optional[int] = None
    salary_range_max: Optional[int] = None
    location: Optional[str] = None
    is_remote: Optional[bool] = None
    cutoff_score: Optional[float] = None

class CampaignResponse(CampaignBase):
    id: str
    organization_id: str
    created_at: datetime
    updated_at: datetime
    organization_name: Optional[str] = None

    class Config:
        from_attributes = True

class CampaignApplicantResponse(BaseModel):
    interview_id: str
    status: str
    ats_score: Optional[float]
    interview_score: Optional[float]
    final_score: Optional[float]
    is_shortlisted: bool
    applied_at: Optional[datetime]
    candidate: CandidateResponse

    class Config:
        from_attributes = True
        
class ApplicantStatusUpdate(BaseModel):
    status: Optional[str] = None # e.g., "rejected", "in_progress"
    is_shortlisted: Optional[bool] = None
    scheduled_at: Optional[datetime] = None
