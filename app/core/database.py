from typing import AsyncGenerator, Optional
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy.pool import NullPool
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.logging import logger

Base = declarative_base()

_engine = None
_async_session_factory = None


def get_database_url() -> str:
    db_url = settings.DATABASE_URL
    if not db_url:
        return ""
    if db_url.startswith("postgres://"):
        db_url = db_url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif db_url.startswith("postgresql://"):
        db_url = db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    
    if "sslmode=" in db_url:
        import re
        db_url = re.sub(r'[?&]sslmode=[^&]*', '', db_url)
        if db_url.endswith('?') or db_url.endswith('&'):
            db_url = db_url[:-1]
    
    return db_url


def create_engine():
    global _engine
    db_url = get_database_url()
    
    if not db_url:
        logger.warning("DATABASE_URL not set, database features will be disabled")
        return None
    
    _engine = create_async_engine(
        db_url,
        echo=settings.DATABASE_ECHO,
        pool_size=settings.DATABASE_POOL_SIZE,
        max_overflow=settings.DATABASE_MAX_OVERFLOW,
        pool_timeout=settings.DATABASE_POOL_TIMEOUT,
        pool_pre_ping=True,
    )
    return _engine


def get_engine():
    global _engine
    if _engine is None:
        create_engine()
    return _engine


def get_session_factory():
    global _async_session_factory
    engine = get_engine()
    
    if engine is None:
        return None
    
    if _async_session_factory is None:
        _async_session_factory = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False
        )
    return _async_session_factory


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    
    if session_factory is None:
        raise RuntimeError("Database not configured. Please set DATABASE_URL environment variable.")
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    session_factory = get_session_factory()
    
    if session_factory is None:
        raise RuntimeError("Database not configured. Please set DATABASE_URL environment variable.")
    
    async with session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    engine = get_engine()
    if engine is None:
        logger.warning("Skipping database initialization - DATABASE_URL not set")
        return
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")


async def close_db() -> None:
    global _engine, _async_session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _async_session_factory = None
        logger.info("Database connection closed")


async def check_db_connection() -> bool:
    engine = get_engine()
    if engine is None:
        return False
    
    try:
        from sqlalchemy import text
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database connection check failed: {e}")
        return False
