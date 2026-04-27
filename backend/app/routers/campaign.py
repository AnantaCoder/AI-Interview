from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy import select
from app.db.session import get_session_maker
from app.deps import get_current_organization
from app.schemas.campaign import CampaignCreate, CampaignUpdate, CampaignResponse
from app.db.models.job_role import JobRole
from app.db.models.organization import Organization

router = APIRouter(prefix="/campaigns", tags=["Campaigns"])

@router.get("/", response_model=List[CampaignResponse])
async def list_campaigns(org: Organization = Depends(get_current_organization)):
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(JobRole).where(JobRole.organization_id == org.id)
        )
        campaigns = result.scalars().all()
        return campaigns

@router.post("/", response_model=CampaignResponse)
async def create_campaign(campaign: CampaignCreate, org: Organization = Depends(get_current_organization)):
    session_maker = get_session_maker()
    async with session_maker() as session:
        new_campaign = JobRole(
            organization_id=org.id,
            **campaign.model_dump()
        )
        session.add(new_campaign)
        await session.commit()
        await session.refresh(new_campaign)
        return new_campaign

@router.get("/{id}", response_model=CampaignResponse)
async def get_campaign(id: str, org: Organization = Depends(get_current_organization)):
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(JobRole).where(JobRole.id == id, JobRole.organization_id == org.id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
        return campaign

@router.patch("/{id}", response_model=CampaignResponse)
async def update_campaign(id: str, campaign_update: CampaignUpdate, org: Organization = Depends(get_current_organization)):
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(JobRole).where(JobRole.id == id, JobRole.organization_id == org.id)
        )
        campaign = result.scalar_one_or_none()
        if not campaign:
            raise HTTPException(status_code=404, detail="Campaign not found")
            
        update_data = campaign_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(campaign, key, value)
            
        await session.commit()
        await session.refresh(campaign)
        return campaign
