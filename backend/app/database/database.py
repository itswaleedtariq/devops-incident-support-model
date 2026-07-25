"""
Database engine and connection manager.

``DatabaseManager`` owns the SQLAlchemy async engine lifecycle:

* ``connect()``    — Create the engine (lazy; does not open connections).
* ``disconnect()`` — Dispose the engine and release pooled connections.
* ``ping()``       — Execute ``SELECT 1`` to verify connectivity.
* ``engine``       — Property exposing the underlying ``AsyncEngine``.

A module-level singleton ``db_manager`` is provided for use throughout
the application.  It is wired into the FastAPI lifespan in ``app.main``.
"""

from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from app.core.logging import get_logger

logger = get_logger("database.manager")


class DatabaseManager:
    """
    Manages the SQLAlchemy async engine lifecycle.

    The engine is created lazily inside ``connect()`` so the class can be
    instantiated at module import time without requiring a live database or
    finalized configuration.
    """

    def __init__(self) -> None:
        self._engine: AsyncEngine | None = None

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        """
        Create the async engine from current application settings.

        This method is idempotent: calling it a second time without an
        intervening ``disconnect()`` is a no-op.

        Note:
            ``create_async_engine`` is lazy — no database socket is opened
            until the first query is executed. This means ``connect()``
            always succeeds regardless of database availability.
        """
        if self._engine is not None:
            logger.debug("DatabaseManager.connect() — engine already exists, skipping.")
            return

        # Import settings here (not at module level) so that test fixtures
        # can override APP_ENV before the engine URL is resolved.
        from app.config.settings import settings

        pool_kwargs: dict = {
            "pool_pre_ping": True,           # Validate connections before use
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "echo": settings.DB_ECHO,
        }

        if settings.DB_USE_NULL_POOL:
            # NullPool: no idle connections — useful for tests and CLI scripts.
            pool_kwargs["poolclass"] = NullPool
        else:
            pool_kwargs["pool_size"] = settings.DB_POOL_SIZE
            pool_kwargs["max_overflow"] = settings.DB_MAX_OVERFLOW
            pool_kwargs["pool_timeout"] = settings.DB_POOL_TIMEOUT

        self._engine = create_async_engine(
            settings.async_database_url,
            **pool_kwargs,
        )

        logger.info(
            "Database engine created [host=%s port=%s db=%s pool_size=%s]",
            settings.DATABASE_HOST,
            settings.DATABASE_PORT,
            settings.DATABASE_NAME,
            settings.DB_POOL_SIZE if not settings.DB_USE_NULL_POOL else "NullPool",
        )

    async def disconnect(self) -> None:
        """
        Dispose the engine and release all pooled connections.

        Safe to call even if ``connect()`` was never called.
        """
        if self._engine is None:
            logger.debug("DatabaseManager.disconnect() — no engine to dispose.")
            return

        await self._engine.dispose()
        self._engine = None
        logger.info("Database engine disposed.")

    # ------------------------------------------------------------------
    # Health
    # ------------------------------------------------------------------

    async def ping(self) -> bool:
        """
        Execute a lightweight ``SELECT 1`` to verify database connectivity.

        Returns:
            ``True`` if the database is reachable, ``False`` otherwise.
            Never raises — all exceptions are caught and logged.
        """
        if self._engine is None:
            logger.warning("Database ping failed: engine not initialized.")
            return False

        try:
            async with self._engine.connect() as conn:
                await conn.execute(text("SELECT 1"))
            logger.debug("Database ping: OK")
            return True
        except Exception as exc:  # noqa: BLE001
            logger.warning("Database ping failed: %s", exc)
            return False

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def engine(self) -> AsyncEngine:
        """
        Return the underlying ``AsyncEngine``.

        Raises:
            RuntimeError: If ``connect()`` has not been called yet.
        """
        if self._engine is None:
            raise RuntimeError(
                "Database engine is not initialized. "
                "Ensure ``await db_manager.connect()`` is called during application startup."
            )
        return self._engine

    @property
    def is_connected(self) -> bool:
        """Return ``True`` if the engine has been created."""
        return self._engine is not None


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

#: Application-wide database manager.
#: Wired into the FastAPI lifespan inside ``app.main.create_app``.
db_manager: DatabaseManager = DatabaseManager()
