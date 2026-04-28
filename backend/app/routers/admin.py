from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select, func
from typing import List

from app.db.session import get_session_maker
from app.deps import get_current_admin
from app.schemas.auth import UserProfile
from app.schemas.admin import PaginatedUserResponse, UserStatusUpdate, AnalyticsResponse

from app.db.models.user import User
from app.db.models.candidate import Candidate
from app.db.models.organization import Organization
from app.db.models.job_role import JobRole
from app.db.models.interview import Interview

router = APIRouter(prefix="/admin", tags=["Admin"])

@router.get("/users", response_model=PaginatedUserResponse)
async def get_all_users(
    skip: int = 0, 
    limit: int = 50,
    admin: UserProfile = Depends(get_current_admin)
):
    """Fetch a paginated list of all users."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Get total count
        count_result = await session.execute(select(func.count()).select_from(User))
        total = count_result.scalar() or 0
        
        # Get paginated users
        result = await session.execute(
            select(User).offset(skip).limit(limit).order_by(User.created_at.desc())
        )
        users = result.scalars().all()
        
        # Convert models to UserProfile schema
        user_profiles = []
        for u in users:
            user_type = u.user_type.value if hasattr(u.user_type, 'value') else str(u.user_type)
            user_profiles.append(
                UserProfile(
                    id=str(u.id),
                    email=u.email,
                    user_type=user_type,
                    full_name=u.full_name,
                    is_active=u.is_active,
                    created_at=u.created_at
                )
            )
            
        return PaginatedUserResponse(total=total, items=user_profiles)

@router.patch("/users/{user_id}/status")
async def update_user_status(
    user_id: str,
    status_update: UserStatusUpdate,
    admin: UserProfile = Depends(get_current_admin)
):
    """Ban/disable or verify a user account."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
            
        if status_update.is_active is not None:
            user.is_active = status_update.is_active
        if status_update.email_verified is not None:
            user.email_verified = status_update.email_verified
            
        await session.commit()
        return {"success": True, "message": "User status updated"}

@router.get("/analytics", response_model=AnalyticsResponse)
async def get_analytics(admin: UserProfile = Depends(get_current_admin)):
    """Fetch global platform metrics."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        # Count candidates
        cand_res = await session.execute(select(func.count()).select_from(Candidate))
        # Count organizations
        org_res = await session.execute(select(func.count()).select_from(Organization))
        # Count campaigns
        camp_res = await session.execute(select(func.count()).select_from(JobRole))
        # Count interviews
        int_res = await session.execute(select(func.count()).select_from(Interview))
        
        return AnalyticsResponse(
            total_candidates=cand_res.scalar() or 0,
            total_organizations=org_res.scalar() or 0,
            total_campaigns=camp_res.scalar() or 0,
            total_interviews=int_res.scalar() or 0,
        )

@router.delete("/campaigns/{id}")
async def delete_campaign(id: str, admin: UserProfile = Depends(get_current_admin)):
    """Admin ability to delete any campaign that violates terms."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(select(JobRole).where(JobRole.id == id))
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        await session.delete(campaign)
        await session.commit()
        return {"success": True, "message": "Campaign deleted"}
