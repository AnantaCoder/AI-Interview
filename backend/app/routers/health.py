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
    description="Returns the basic health status of the API service including database connectivity."
)
async def health_check() -> HealthResponse:
    settings = get_settings()
    
    # Check database connection
    try:
        engine = get_engine()
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception:
        db_status = "disconnected"
    
    return HealthResponse(
        status="healthy",
        version=settings.app_version,
        database=db_status
    )




