from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select

from app.db.session import get_session_maker
from app.deps import get_current_organization
from app.schemas.organization import OrganizationResponse, OrganizationUpdate
from app.db.models.organization import Organization
from app.config.logging import get_logger

logger = get_logger("routers.organization")

router = APIRouter(prefix="/organization", tags=["Organization"])

@router.get("/profile", response_model=OrganizationResponse)
async def get_organization_profile(
    org: Organization = Depends(get_current_organization)
):
    """Fetch the authenticated organization's profile."""
    return org

@router.put("/profile", response_model=OrganizationResponse)
async def update_organization_profile(
    update_data: OrganizationUpdate,
    org: Organization = Depends(get_current_organization) #fastapi dependancy injection
):
    """Update organization details (logo, website, description, etc)."""
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(Organization).where(Organization.id == org.id)
        )
        db_org = result.scalar_one_or_none()
        if not db_org:
            raise HTTPException(status_code=404, detail="Organization not found")

        changes = update_data.model_dump(exclude_unset=True)
        for key, value in changes.items():
            setattr(db_org, key, value)

        await session.commit()
        await session.refresh(db_org)
        session.expunge(db_org)
        return db_org