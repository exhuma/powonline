import os
from configparser import ConfigParser
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from powonline.config import default
from powonline.model import get_dsn

# Global variables for lazy initialization
_engine: AsyncEngine | None = None
_async_session: async_sessionmaker[AsyncSession] | None = None


def get_engine() -> AsyncEngine:
    """Get or create the database engine (lazy initialization)."""
    global _engine
    if _engine is None:
        database_url = get_dsn()
        if not database_url:
            raise ValueError(
                "Database URL not configured. Set POWONLINE_DSN environment variable."
            )
        _engine = create_async_engine(database_url)
    return _engine


def get_async_session_maker() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session maker (lazy initialization)."""
    global _async_session
    if _async_session is None:
        engine = get_engine()
        _async_session = async_sessionmaker(
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
            bind=engine,
        )
    return _async_session


def set_engine(engine: AsyncEngine) -> None:
    """Set a custom engine (useful for testing)."""
    global _engine, _async_session
    _engine = engine
    _async_session = None  # Reset session maker


def set_async_session_maker(
    session_maker: async_sessionmaker[AsyncSession],
) -> None:
    """Set a custom session maker (useful for testing)."""
    global _async_session
    _async_session = session_maker


async def get_db():
    """Dependency to get a database session."""
    session_maker = get_async_session_maker()
    async with session_maker() as session:
        yield session
        await session.commit()
