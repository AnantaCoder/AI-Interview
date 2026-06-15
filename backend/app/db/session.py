from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
from typing import AsyncGenerator

from app.config.settings import get_settings
from app.config.logging import get_logger

logger = get_logger("db.session")

Base = declarative_base()

_engine = None
_async_session_maker = None


def get_database_url() -> tuple[str, dict]:
    """
    Convert the DATABASE_URL to an async-compatible connection string and
    return (url, connect_args) so callers can pass driver-specific options.

    Handles:
      - sqlite:// → sqlite+aiosqlite://
      - postgres:// / postgresql:// → postgresql+asyncpg://
      - Strips ?sslmode=require from Neon/Postgres URLs and returns
        connect_args={"ssl": "require"} instead (asyncpg doesn't accept
        sslmode as a query parameter).
    """
    settings = get_settings()
    database_url = settings.database_url
    connect_args: dict = {}

    # SQLite
    if database_url.startswith("sqlite://"):
        if "+aiosqlite" not in database_url:
            database_url = database_url.replace("sqlite://", "sqlite+aiosqlite://", 1)
        connect_args["check_same_thread"] = False
        return database_url, connect_args

    # PostgreSQL – normalise scheme
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif database_url.startswith("postgresql://") and "+asyncpg" not in database_url:
        database_url = database_url.replace("postgresql://", "postgresql+asyncpg://", 1)

    # asyncpg cannot parse ?sslmode=… — strip it and pass via connect_args
    if "sslmode=require" in database_url:
        database_url = database_url.replace("?sslmode=require", "").replace("&sslmode=require", "")
        connect_args["ssl"] = "require"
    elif "sslmode=" in database_url:
        import re
        database_url = re.sub(r"[?&]sslmode=[^&]*", "", database_url)

    return database_url, connect_args


def get_engine():
    global _engine
    if _engine is None: #None coz initially no db engine is present 
        settings = get_settings()
        database_url, connect_args = get_database_url()
        is_sqlite = "sqlite" in database_url

        _engine = create_async_engine(
            database_url,
            echo=settings.debug,
            pool_pre_ping=not is_sqlite,
            connect_args=connect_args,
        )
        # Log only the host portion for security
        if "@" in database_url:
            safe_url = database_url.split("@")[-1]
        else:
            safe_url = database_url.split("///")[-1] if "///" in database_url else database_url
        logger.info(f"Database engine created for: {safe_url}")
    return _engine


def get_session_maker():
    global _async_session_maker
    if _async_session_maker is None:
        _async_session_maker = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
        )
    return _async_session_maker


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
    from app.db.models import User, Organization, Candidate, JobRole, Interview, InterviewQuestion, InterviewResponse, ProctorSession

    logger.info("Creating database tables...")
    try:
        engine = get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            
            # Ensure expected_answer column is added to interview_questions if it doesn't exist
            # Ensure video proctoring columns are added to interviews if they don't exist
            url_str = str(engine.url)
            if "postgresql" in url_str:
                await conn.execute(
                    text("ALTER TABLE interview_questions ADD COLUMN IF NOT EXISTS expected_answer TEXT;")
                )
                await conn.execute(
                    text("ALTER TABLE interviews ADD COLUMN IF NOT EXISTS video_confidence_score DOUBLE PRECISION;")
                )
                await conn.execute(
                    text("ALTER TABLE interviews ADD COLUMN IF NOT EXISTS video_attention_score DOUBLE PRECISION;")
                )
                await conn.execute(
                    text("ALTER TABLE interviews ADD COLUMN IF NOT EXISTS video_integrity_score DOUBLE PRECISION;")
                )
                logger.info("Executed ALTER TABLE migrations for PostgreSQL columns")
            elif "sqlite" in url_str:
                try:
                    await conn.execute(
                        text("ALTER TABLE interview_questions ADD COLUMN expected_answer TEXT;")
                    )
                except Exception:
                    pass
                try:
                    await conn.execute(
                        text("ALTER TABLE interviews ADD COLUMN video_confidence_score DOUBLE PRECISION;")
                    )
                except Exception:
                    pass
                try:
                    await conn.execute(
                        text("ALTER TABLE interviews ADD COLUMN video_attention_score DOUBLE PRECISION;")
                    )
                except Exception:
                    pass
                try:
                    await conn.execute(
                        text("ALTER TABLE interviews ADD COLUMN video_integrity_score DOUBLE PRECISION;")
                    )
                except Exception:
                    pass
                logger.info("Executed ALTER TABLE migrations for SQLite columns")
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
