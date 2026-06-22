from fastapi import APIRouter
from app.config.settings import get_settings
from app.routers import (
    health,
    auth,
    resume,
    ats,
    campaign,
    candidate,
    organization,
    admin,
    interview,
    proctoring,
)

api_router = APIRouter()
settings = get_settings()

# mother of all routes :  Include all sub-routers with the /api/v1 prefix
api_router.include_router(health.router, prefix="/api/v1")
api_router.include_router(auth.router, prefix="/api/v1")
api_router.include_router(resume.router, prefix="/api/v1")
api_router.include_router(ats.router, prefix="/api/v1")
api_router.include_router(campaign.router, prefix="/api/v1")
api_router.include_router(candidate.router, prefix="/api/v1")
api_router.include_router(organization.router, prefix="/api/v1")
api_router.include_router(admin.router, prefix="/api/v1")
api_router.include_router(interview.router, prefix="/api/v1")
api_router.include_router(proctoring.router, prefix="/api/v1")


@api_router.get("/", summary="Root endpoint", description="API root with welcome message")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs"
    }
