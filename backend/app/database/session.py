"""
Database session factory and FastAPI dependency.

``get_session_factory`` — Build an ``async_sessionmaker`` bound to an engine.
``get_db``              — FastAPI ``Depends`` callable that yields a managed
                          ``AsyncSession`` with automatic commit / rollback.

Usage in endpoint handlers (Milestone 2.2+)::

    from fastapi import Depends
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database.session import get_db

    @router.get("/incidents")
    async def list_incidents(db: AsyncSession = Depends(get_db)):
        result = await db.execute(select(Incident))
        return result.scalars().all()
"""

from __future__ import annotations

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from app.core.logging import get_logger

logger = get_logger("database.session")


def get_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    """
    Create a reusable session factory bound to *engine*.

    Args:
        engine: The ``AsyncEngine`` to bind sessions to.

    Returns:
        An ``async_sessionmaker`` configured for production use:

        - ``expire_on_commit=False`` — avoids lazy-load errors after commit.
        - ``autocommit=False`` — explicit transaction control.
        - ``autoflush=False`` — flushed manually or on commit only.
    """
    return async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


async def get_db() -> AsyncIterator[AsyncSession]:
    """
    FastAPI dependency that provides a transactional ``AsyncSession``.

    The session is committed automatically on success or rolled back on any
    exception.  The session is always closed regardless of the outcome.

    Yields:
        An open ``AsyncSession`` ready for use.

    Raises:
        RuntimeError: If the database engine has not been initialized.

    Example::

        @router.post("/incidents")
        async def create_incident(
            payload: IncidentCreate,
            db: AsyncSession = Depends(get_db),
        ) -> Incident:
            ...
    """
    from app.database.database import db_manager

    factory = get_session_factory(db_manager.engine)

    async with factory() as session:
        try:
            logger.debug("Database session opened.")
            yield session
            await session.commit()
            logger.debug("Database session committed.")
        except Exception:
            await session.rollback()
            logger.warning("Database session rolled back due to exception.")
            raise
