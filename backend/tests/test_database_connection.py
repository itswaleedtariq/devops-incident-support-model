"""
Database connection and session tests.

Unit tests (no live database required):
    - Engine creation does not raise without a live database.
    - Ping returns ``False`` gracefully when no database is available.
    - Session factory creates an ``AsyncSession`` instance.
    - ``DatabaseManager`` lifecycle (connect / disconnect) is idempotent.

Integration tests (require a live PostgreSQL instance):
    Marked ``pytest.mark.integration`` — skipped by default.
    Run with: ``pytest -m integration``
"""

from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession


# ---------------------------------------------------------------------------
# Unit tests — no live database required
# ---------------------------------------------------------------------------


class TestDatabaseManagerLifecycle:
    """Verify the DatabaseManager lifecycle without a real database."""

    @pytest.mark.asyncio
    async def test_connect_does_not_raise(self) -> None:
        """
        ``connect()`` only creates the engine object; it does NOT open a
        socket.  This must succeed even without a running database.
        """
        from app.database.database import DatabaseManager

        manager = DatabaseManager()
        await manager.connect()
        assert manager.is_connected is True
        await manager.disconnect()

    @pytest.mark.asyncio
    async def test_disconnect_without_connect_is_safe(self) -> None:
        """Calling ``disconnect()`` before ``connect()`` must not raise."""
        from app.database.database import DatabaseManager

        manager = DatabaseManager()
        await manager.disconnect()  # Should be a silent no-op

    @pytest.mark.asyncio
    async def test_double_connect_is_idempotent(self) -> None:
        """Calling ``connect()`` twice should be safe (no duplicate engines)."""
        from app.database.database import DatabaseManager

        manager = DatabaseManager()
        await manager.connect()
        engine_id = id(manager.engine)
        await manager.connect()  # Should reuse the existing engine
        assert id(manager.engine) == engine_id
        await manager.disconnect()

    @pytest.mark.asyncio
    async def test_ping_returns_false_without_real_db(self) -> None:
        """
        ``ping()`` should return ``False`` — not raise — when the database
        is unreachable.
        """
        from app.database.database import DatabaseManager

        manager = DatabaseManager()
        await manager.connect()
        result = await manager.ping()
        assert isinstance(result, bool)
        await manager.disconnect()

    @pytest.mark.asyncio
    async def test_ping_returns_false_before_connect(self) -> None:
        """``ping()`` called before ``connect()`` should return ``False``."""
        from app.database.database import DatabaseManager

        manager = DatabaseManager()
        result = await manager.ping()
        assert result is False

    def test_engine_raises_before_connect(self) -> None:
        """Accessing ``.engine`` before ``connect()`` must raise ``RuntimeError``."""
        from app.database.database import DatabaseManager

        manager = DatabaseManager()
        with pytest.raises(RuntimeError, match="not initialized"):
            _ = manager.engine

    @pytest.mark.asyncio
    async def test_disconnect_clears_engine(self) -> None:
        """After ``disconnect()``, ``is_connected`` must be ``False``."""
        from app.database.database import DatabaseManager

        manager = DatabaseManager()
        await manager.connect()
        await manager.disconnect()
        assert manager.is_connected is False


class TestSessionFactory:
    """Verify session factory construction."""

    @pytest.mark.asyncio
    async def test_factory_creates_async_session(self) -> None:
        """``get_session_factory`` should return an ``AsyncSession`` factory."""
        from app.database.database import DatabaseManager
        from app.database.session import get_session_factory

        manager = DatabaseManager()
        await manager.connect()

        factory = get_session_factory(manager.engine)
        session = factory()
        assert isinstance(session, AsyncSession)
        await session.close()
        await manager.disconnect()


# ---------------------------------------------------------------------------
# Integration tests — require a live PostgreSQL instance
# ---------------------------------------------------------------------------


@pytest.mark.integration
class TestDatabaseIntegration:
    """
    Integration tests that require a running PostgreSQL instance.

    Run with::

        pytest -m integration

    Configure the database via environment variables or ``.env``.
    """

    @pytest.mark.asyncio
    async def test_ping_succeeds_with_real_db(self) -> None:
        """Ping must return ``True`` when PostgreSQL is available."""
        from app.database.database import DatabaseManager

        manager = DatabaseManager()
        await manager.connect()
        result = await manager.ping()
        assert result is True, (
            "Database ping failed. Ensure PostgreSQL is running and "
            "DATABASE_* environment variables are configured correctly."
        )
        await manager.disconnect()

    @pytest.mark.asyncio
    async def test_session_can_execute_query(self) -> None:
        """A real session should execute a SELECT 1 without error."""
        from sqlalchemy import text

        from app.database.database import DatabaseManager
        from app.database.session import get_session_factory

        manager = DatabaseManager()
        await manager.connect()
        factory = get_session_factory(manager.engine)

        async with factory() as session:
            result = await session.execute(text("SELECT 1"))
            assert result.scalar() == 1

        await manager.disconnect()
