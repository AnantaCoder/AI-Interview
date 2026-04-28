from pydantic import BaseModel
from typing import List, Optional
from app.schemas.auth import UserProfile

class PaginatedUserResponse(BaseModel):
    total: int
    items: List[UserProfile]

class UserStatusUpdate(BaseModel):
    is_active: Optional[bool] = None
    email_verified: Optional[str] = None

class AnalyticsResponse(BaseModel):
    total_candidates: int
    total_organizations: int
    total_campaigns: int
    total_interviews: int
