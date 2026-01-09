from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config.settings import get_settings
from app.config.logging import setup_logging, get_logger
from app.db.session import init_db, close_db
from app.exceptions.handlers import register_exception_handlers
from app.routers import health, auth

logger = get_logger("main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting AI Interview Analysis API...")
    
    await init_db()
    
    yield
    
    await close_db()
    logger.info("Shutting down AI Interview Analysis API...")


def create_app() -> FastAPI:
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered interview analysis system for automated recruitment",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan
    )
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    register_exception_handlers(app)
    
    app.include_router(health.router, prefix="/api/v1")
    app.include_router(auth.router, prefix="/api/v1")
    
    @app.get("/", summary="Root endpoint", description="API root with welcome message")
    async def root():
        return {
            "message": f"Welcome to {settings.app_name}",
            "version": settings.app_version,
            "docs": "/docs"
        }
    
    return app


app = create_app()
