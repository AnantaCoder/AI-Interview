from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config.settings import get_settings
from app.config.logging import setup_logging, get_logger
from app.db.session import init_db, close_db
from app.exceptions.handlers import register_exception_handlers
from app.routers.api import api_router
from app.middleware.logging import RequestLoggingMiddleware

logger = get_logger("main")


# asynccontextmanager-> helps for the define start-up and clean-up logic
@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    logger.info("Starting AI Interview Analysis API...")
    await init_db()
    yield  # <-- application will run here
    await close_db()
    logger.info("Shutting down AI Interview Analysis API...")


def create_app() -> FastAPI:
    settings = get_settings()
    print("CORS ORIGINS LOADED:", settings.cors_origins)

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="AI-powered interview analysis system for automated recruitment",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,  # startup code above (with lifespan the application will start and run the startup code then enter into yield otherwise each request will run the startup code and clean up which will waste/slow the momory )
    )

    """middleware allows clients from different origins to access the api"""
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Custom request logging middleware
    app.add_middleware(RequestLoggingMiddleware)

    # Register exception handlers
    register_exception_handlers(app)

    # Include central API routes to all endpoints 
    app.include_router(api_router)

    return app


app = create_app()

