from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from typing import AsyncGenerator, Optional

from app.config.settings import get_settings
from app.config.logging import get_logger

logger = get_logger("db.session")

Base = declarative_base()

_engine = None
_async_session_maker = None


def get_database_url() -> str:
    """Get PostgreSQL database URL with asyncpg driver."""
    settings = get_settings()
    database_url = settings.database_url
    
    # Convert postgres:// or postgresql:// to postgresql+asyncpg://
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    return database_url


def get_engine():
    global _engine
    if _engine is None:
        settings = get_settings()
        database_url = get_database_url()
        
        _engine = create_async_engine(
            database_url,
            echo=settings.debug,
            pool_pre_ping=True,
        )
        logger.info(f"Database engine created for: {database_url.split('@')[-1] if '@' in database_url else 'local'}")
    return _engine


def get_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return _async_session_maker


# For backwards compatibility
engine = property(lambda self: get_engine())
AsyncSessionLocal = property(lambda self: get_session_maker())


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_maker = get_session_maker()
    async with session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_tables() -> None:
    """Create all tables in the database from SQLAlchemy models."""
    # Import all models to register them with Base
    from app.db.models import User, Organization, Candidate, JobRole, Interview, InterviewQuestion, InterviewResponse
    
    logger.info("Creating database tables...")
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("Database tables created successfully")
    except Exception as e:
        logger.error(f"Failed to create tables: {e}")
        raise


async def init_db(create_tables_on_startup: bool = True) -> None:
    logger.info("Initializing database connection...")
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            pass
        logger.info("Database connection established")
        
        # Create tables if they don't exist
        if create_tables_on_startup:
            await create_tables()
    except Exception as e:
        logger.warning(f"Database connection failed: {e}")


async def close_db() -> None:
    global _engine, _async_session_maker
    logger.info("Closing database connection...")
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_maker = None
    logger.info("Database connection closed")
