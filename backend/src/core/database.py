"""SQLAlchemy 2.0 async database engine, session factory, and dependency."""

import os
from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from src.core.config import get_settings

settings = get_settings()

# Pool sizing:
# - Each connection holds memory both in Python and in PgBouncer/Postgres.
# - With 1 uvicorn worker and light traffic, 5 base + 5 overflow = 10 max
#   keeps memory low while still allowing short bursts.
# - SAVVY_DB_POOL_SIZE / SAVVY_DB_MAX_OVERFLOW override per-environment
#   without code change.
_POOL_SIZE = int(os.environ.get("SAVVY_DB_POOL_SIZE", "5"))
_MAX_OVERFLOW = int(os.environ.get("SAVVY_DB_MAX_OVERFLOW", "5"))

# SQL echo eats memory (string formatting + logger buffers) — only ON when
# explicitly requested via SAVVY_SQL_ECHO=1, regardless of APP_ENV.
_SQL_ECHO = os.environ.get("SAVVY_SQL_ECHO", "").lower() in ("1", "true", "yes")

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=_SQL_ECHO,
    pool_size=_POOL_SIZE,
    max_overflow=_MAX_OVERFLOW,
    pool_pre_ping=True,
    # Supabase uses PgBouncer (port 6543) which doesn't support prepared statements
    connect_args={"statement_cache_size": 0, "prepared_statement_cache_size": 0},
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Declarative base for all ORM models."""


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency that yields an async database session.

    The session is committed on success and rolled back on exception.
    """
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
