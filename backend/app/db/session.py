"""
Async SQLAlchemy session factory.
BUG-21 FIX: Only commit if session has pending changes — no wasted round-trips on GETs.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    create_async_engine,
    async_sessionmaker,
)
from sqlalchemy.orm import DeclarativeBase
from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,    # Reconnects on stale connections (critical for Supabase idle timeouts)
    pool_recycle=3600,     # Recycle connections every hour
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Prevents lazy-load errors in async context after commit
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            # BUG-21 FIX: Only commit if there are actual pending changes.
            # GET endpoints (history, get_analysis) do zero writes —
            # the old code was doing a wasted COMMIT on every single read request.
            if session.in_transaction():
                await session.commit()
        except Exception:
            await session.rollback()
            raise
