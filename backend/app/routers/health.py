from fastapi import APIRouter
from sqlalchemy import text

from app.config.settings import get_settings
from app.db.session import get_engine
from app.schemas.responses import HealthResponse

router = APIRouter(prefix="/health", tags=["Health"])


@router.get(
    "",
    response_model=HealthResponse,
    summary="Basic health check",
    description="Returns the basic health status of the API service."
)
async def health_check() -> HealthResponse:
    settings = get_settings()
    return HealthResponse(
        status="healthy",
        version=settings.app_version
    )


@router.get(
    "/db",
    response_model=HealthResponse,
    summary="Database health check",
    description="Checks the database connectivity and returns the status."
)
async def database_health_check() -> HealthResponse:
    settings = get_settings()
    
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
        status = "healthy"
    except Exception as e:
        db_status = f"disconnected: {str(e)}"
        status = "unhealthy"
    
    return HealthResponse(
        status=status,
        version=settings.app_version,
        database=db_status
    )

