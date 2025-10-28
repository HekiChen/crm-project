"""
Database configuration and connection management.
"""
from typing import AsyncGenerator, Optional
from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine, AsyncEngine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


# Lazy engine/session creation to avoid importing DB drivers at module-import time.
# This makes importing `app.main` safe in environments where the DB driver isn't
# installed (e.g., for lightweight tooling or preliminary imports).
engine: Optional[AsyncEngine] = None
AsyncSessionLocal: Optional[async_sessionmaker] = None


def _ensure_engine() -> None:
    """Create the SQLAlchemy async engine and session factory if not present."""
    global engine, AsyncSessionLocal
    if engine is None or AsyncSessionLocal is None:
        engine = create_async_engine(
            settings.database_url,
            echo=settings.debug,
            pool_pre_ping=True,
            pool_recycle=300,
        )

        AsyncSessionLocal = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )


class Base(DeclarativeBase):
    """Base class for all database models."""
    
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_%(constraint_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s"
        }
    )


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    # Ensure engine and session factory exist before creating a session
    _ensure_engine()
    assert AsyncSessionLocal is not None
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables."""
    _ensure_engine()
    assert engine is not None
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def close_db() -> None:
    """Close database connections."""
    if engine is not None:
        await engine.dispose()