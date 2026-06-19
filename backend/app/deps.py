"""
FastAPI dependencies for authentication and database sessions.
"""
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy import select

from app.db.session import get_session_maker
from app.db.models.user import User
from app.utils.security import verify_access_token
from app.schemas.auth import UserProfile
from app.config.logging import get_logger

logger = get_logger("deps")

# This will show the lock icon on protected endpoints in /docs
bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> UserProfile:
    """
    FastAPI dependency – extracts and validates the Bearer JWT token,
    then loads the User from the database.
    """
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    payload = verify_access_token(credentials.credentials)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload["sub"]

    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
        )

    return UserProfile.model_validate(user)


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(bearer_scheme),
) -> Optional[UserProfile]:
    """Same as get_current_user but returns None instead of raising."""
    if credentials is None:
        return None
    try:
        return await get_current_user(credentials)
    except HTTPException:
        return None

async def get_current_organization(
    current_user: UserProfile = Depends(get_current_user),
):
    """
    FastAPI dependency – restricts access to organizations only,
    and returns the Organization database record. If the record
    doesn't exist yet, it creates one.
    """
    from app.db.models.organization import Organization
    
    if current_user.user_type != "organization":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires organization privileges",
        )
        
    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(Organization).where(Organization.user_id == current_user.id)
        )
        org = result.scalar_one_or_none()
        
        if not org:
            org = Organization(
                user_id=current_user.id,
                name=current_user.full_name or "My Organization",
                contact_email=current_user.email
            )
            session.add(org)
            await session.commit()
            await session.refresh(org)
            
        session.expunge(org)
        return org


async def get_current_candidate(
    current_user: UserProfile = Depends(get_current_user),
    ):
    """
    FastAPI dependency – restricts access to candidates only,
    and returns the Candidate database record. If the record
    doesn't exist yet, it creates one (lazy creation).
    """

    from app.db.models.candidate import Candidate

    if current_user.user_type!="candidate":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires candidate privileges",
        )

    session_maker = get_session_maker()
    async with session_maker() as session:
        result = await session.execute(
            select(Candidate).where(Candidate.user_id == current_user.id)
        )
        candidate = result.scalar_one_or_none()
        
        if not candidate:
            candidate = Candidate(
                user_id=current_user.id,
                email=current_user.email,
                full_name=current_user.full_name or "Candidate",
            )
            session.add(candidate)
            await session.commit()
            await session.refresh(candidate)
            
        session.expunge(candidate)
        return candidate

async def get_current_admin(
    current_user: UserProfile = Depends(get_current_user),
):
    """
    FastAPI dependency – restricts access to admins only.
    """
    if current_user.user_type != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Requires administrator privileges",
        )
    return current_user
