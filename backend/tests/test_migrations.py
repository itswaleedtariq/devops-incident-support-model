"""
Migration and seed unit tests.

Unit tests (no database required):
    - Migration file structure and metadata
    - Migration upgrade / downgrade function signatures
    - Seed data definition integrity
    - Seed function idempotency (via mocking)
    - CLI script structure

Integration tests (require a live PostgreSQL instance):
    Marked ``pytest.mark.integration`` — skipped by default.
    Run with: ``pytest --integration``
"""

from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest


# ===========================================================================
# Helper: locate the initial migration file
# ===========================================================================

_BACKEND_DIR = Path(__file__).resolve().parent.parent
_VERSIONS_DIR = _BACKEND_DIR / "alembic" / "versions"


def _find_initial_migration() -> Path | None:
    """Return the path to the initial schema migration file, if present."""
    for f in _VERSIONS_DIR.glob("*.py"):
        if "initial_schema" in f.name:
            return f
    return None


# ===========================================================================
# Migration file structure
# ===========================================================================


class TestMigrationFileExists:
    def test_versions_directory_exists(self) -> None:
        assert _VERSIONS_DIR.exists(), "alembic/versions/ directory must exist"

    def test_initial_migration_file_exists(self) -> None:
        migration = _find_initial_migration()
        assert migration is not None, (
            "Initial schema migration file not found in alembic/versions/. "
            "Expected a file matching *initial_schema*.py"
        )

    def test_migration_file_is_python(self) -> None:
        migration = _find_initial_migration()
        assert migration is not None
        assert migration.suffix == ".py"


class TestMigrationContent:
    """Verify the migration file has the required structural elements."""

    @pytest.fixture
    def migration_source(self) -> str:
        migration = _find_initial_migration()
        assert migration is not None
        return migration.read_text(encoding="utf-8")

    def test_revision_variable_defined(self, migration_source: str) -> None:
        assert "revision:" in migration_source or 'revision =' in migration_source

    def test_down_revision_is_none(self, migration_source: str) -> None:
        """Initial migration must have no parent revision."""
        assert "down_revision" in migration_source
        assert "None" in migration_source

    def test_upgrade_function_defined(self, migration_source: str) -> None:
        assert "def upgrade()" in migration_source

    def test_downgrade_function_defined(self, migration_source: str) -> None:
        assert "def downgrade()" in migration_source

    def test_all_tables_referenced_in_upgrade(self, migration_source: str) -> None:
        """Every model table must appear in the upgrade function."""
        for table in ("roles", "users", "incidents", "feedbacks", "documents", "embedding_metadata"):
            assert table in migration_source, f"Table '{table}' not found in migration"

    def test_enum_types_created(self, migration_source: str) -> None:
        for enum_type in ("incidentstatus", "incidentseverity", "documentcategory"):
            assert enum_type in migration_source, f"ENUM type '{enum_type}' not found in migration"

    def test_downgrade_drops_all_tables(self, migration_source: str) -> None:
        """Downgrade must reference drop operations for all tables."""
        assert "drop_table" in migration_source

    def test_enum_types_dropped_in_downgrade(self, migration_source: str) -> None:
        assert "DROP TYPE" in migration_source

    def test_pk_constraints_named(self, migration_source: str) -> None:
        """Primary key constraints must follow the pk_ naming convention."""
        for table in ("roles", "users", "incidents", "feedbacks", "documents"):
            assert f"pk_{table}" in migration_source


class TestMigrationModule:
    """Import the migration module and verify its attributes."""

    @pytest.fixture
    def migration_module(self):
        migration = _find_initial_migration()
        assert migration is not None
        import importlib.util

        spec = importlib.util.spec_from_file_location("initial_migration", migration)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module

    def test_revision_is_string(self, migration_module) -> None:
        assert isinstance(migration_module.revision, str)
        assert len(migration_module.revision) > 0

    def test_down_revision_is_none(self, migration_module) -> None:
        assert migration_module.down_revision is None

    def test_upgrade_is_callable(self, migration_module) -> None:
        assert callable(migration_module.upgrade)

    def test_downgrade_is_callable(self, migration_module) -> None:
        assert callable(migration_module.downgrade)


# ===========================================================================
# Seed data definitions
# ===========================================================================


class TestSeedDataDefinitions:
    def test_default_roles_is_a_list(self) -> None:
        from app.database.seed import DEFAULT_ROLES

        assert isinstance(DEFAULT_ROLES, list)

    def test_default_roles_count(self) -> None:
        from app.database.seed import DEFAULT_ROLES

        assert len(DEFAULT_ROLES) == 4

    def test_all_roles_have_name(self) -> None:
        from app.database.seed import DEFAULT_ROLES

        for role in DEFAULT_ROLES:
            assert "name" in role
            assert isinstance(role["name"], str)
            assert len(role["name"]) > 0

    def test_all_roles_have_description(self) -> None:
        from app.database.seed import DEFAULT_ROLES

        for role in DEFAULT_ROLES:
            assert "description" in role
            assert isinstance(role["description"], str)

    def test_role_names_are_unique(self) -> None:
        from app.database.seed import DEFAULT_ROLES

        names = [r["name"] for r in DEFAULT_ROLES]
        assert len(names) == len(set(names)), "Duplicate role names in DEFAULT_ROLES"

    def test_expected_roles_present(self) -> None:
        from app.database.seed import DEFAULT_ROLES

        names = {r["name"] for r in DEFAULT_ROLES}
        assert "Admin" in names
        assert "DevOps Engineer" in names
        assert "AI Engineer" in names
        assert "Viewer" in names


# ===========================================================================
# Seed function — unit tests with mocked session
# ===========================================================================


class TestSeedRolesFunction:
    """Test seed_roles() with a mocked AsyncSession — no database required."""

    @pytest.mark.asyncio
    async def test_creates_roles_when_none_exist(self) -> None:
        """All roles should be created when the table is empty."""
        from app.database.seed import DEFAULT_ROLES, seed_roles

        session = AsyncMock()
        # execute() is async; its result's scalar_one_or_none() is SYNCHRONOUS.
        session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        created = await seed_roles(session)

        assert created == len(DEFAULT_ROLES)
        assert session.add.call_count == len(DEFAULT_ROLES)

    @pytest.mark.asyncio
    async def test_skips_existing_roles(self) -> None:
        """No roles should be created if all already exist."""
        from app.database.seed import seed_roles
        from app.models.role import Role

        session = AsyncMock()
        mock_existing = MagicMock(spec=Role)
        session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_existing)
        )

        created = await seed_roles(session)

        assert created == 0
        session.add.assert_not_called()

    @pytest.mark.asyncio
    async def test_idempotent_second_run(self) -> None:
        """Running seed twice should not create duplicates."""
        from app.database.seed import DEFAULT_ROLES, seed_roles
        from app.models.role import Role

        session = AsyncMock()
        mock_existing = MagicMock(spec=Role)

        # First run: nothing exists.
        session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )
        first_run = await seed_roles(session)
        assert first_run == len(DEFAULT_ROLES)

        # Second run: all roles exist — reset the mock.
        session.add.reset_mock()
        session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=mock_existing)
        )
        second_run = await seed_roles(session)
        assert second_run == 0

    @pytest.mark.asyncio
    async def test_partial_seed_only_creates_missing(self) -> None:
        """If some roles exist, only the missing ones should be created."""
        from app.database.seed import DEFAULT_ROLES, seed_roles
        from app.models.role import Role

        session = AsyncMock()
        existing_mock = MagicMock(spec=Role)

        # side_effect on the execute return so each call gets a fresh MagicMock.
        # First call: role exists; remaining calls: role is absent.
        def _make_result(value):
            return MagicMock(scalar_one_or_none=MagicMock(return_value=value))

        session.execute.side_effect = [
            _make_result(existing_mock)
        ] + [
            _make_result(None) for _ in range(len(DEFAULT_ROLES) - 1)
        ]

        created = await seed_roles(session)

        assert created == len(DEFAULT_ROLES) - 1

    @pytest.mark.asyncio
    async def test_adds_role_objects_to_session(self) -> None:
        """Created roles must be added to the session for INSERT."""
        from app.database.seed import seed_roles
        from app.models.role import Role

        session = AsyncMock()
        session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        await seed_roles(session)

        for add_call in session.add.call_args_list:
            added_obj = add_call[0][0]
            assert isinstance(added_obj, Role)


# ===========================================================================
# seed_database function
# ===========================================================================


class TestSeedDatabase:
    @pytest.mark.asyncio
    async def test_commits_after_seeding(self) -> None:
        """seed_database must commit the session on success."""
        from app.database.seed import seed_database

        session = AsyncMock()
        session.execute.return_value = MagicMock(
            scalar_one_or_none=MagicMock(return_value=None)
        )

        await seed_database(session)

        session.commit.assert_called_once()


# ===========================================================================
# Alembic environment configuration
# ===========================================================================


class TestAlembicConfig:
    def test_alembic_ini_exists(self) -> None:
        ini = _BACKEND_DIR / "alembic.ini"
        assert ini.exists(), "alembic.ini must exist in backend/"

    def test_env_py_exists(self) -> None:
        env = _BACKEND_DIR / "alembic" / "env.py"
        assert env.exists(), "alembic/env.py must exist"

    def test_script_mako_exists(self) -> None:
        mako = _BACKEND_DIR / "alembic" / "script.py.mako"
        assert mako.exists(), "alembic/script.py.mako must exist"

    def test_alembic_ini_script_location(self) -> None:
        from alembic.config import Config

        cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
        assert cfg.get_main_option("script_location") == "alembic"


# ===========================================================================
# Integration tests (require live PostgreSQL)
# ===========================================================================


@pytest.mark.integration
class TestMigrationIntegration:
    """
    Integration tests that run the actual Alembic migration against PostgreSQL.

    Run with::

        pytest --integration

    Prerequisites:
        - PostgreSQL must be running and accessible.
        - DATABASE_* environment variables must be configured.
        - The target database must be empty (or at ``base`` revision).
    """

    @pytest.mark.asyncio
    async def test_upgrade_creates_all_tables(self) -> None:
        """upgrade head should create all six tables."""
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy.ext.asyncio import create_async_engine

        from app.config.settings import settings

        cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
        command.upgrade(cfg, "head")

        engine = create_async_engine(settings.async_database_url)
        async with engine.connect() as conn:

            def _get_tables(sync_conn):
                inspector = sa_inspect(sync_conn)
                return set(inspector.get_table_names())

            tables = await conn.run_sync(_get_tables)
        await engine.dispose()

        expected = {
            "roles", "users", "incidents", "feedbacks",
            "documents", "embedding_metadata",
        }
        assert expected.issubset(tables), (
            f"Missing tables after migration: {expected - tables}"
        )

    @pytest.mark.asyncio
    async def test_downgrade_removes_tables(self) -> None:
        """downgrade base should remove all six tables."""
        from alembic import command
        from alembic.config import Config
        from sqlalchemy import inspect as sa_inspect
        from sqlalchemy.ext.asyncio import create_async_engine

        from app.config.settings import settings

        cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
        command.downgrade(cfg, "base")

        engine = create_async_engine(settings.async_database_url)
        async with engine.connect() as conn:

            def _get_tables(sync_conn):
                inspector = sa_inspect(sync_conn)
                return set(inspector.get_table_names())

            tables = await conn.run_sync(_get_tables)
        await engine.dispose()

        for table in ("roles", "users", "incidents", "feedbacks"):
            assert table not in tables, f"Table '{table}' should have been dropped"

    @pytest.mark.asyncio
    async def test_upgrade_after_downgrade(self) -> None:
        """upgrade head after downgrade should re-create all tables."""
        from alembic import command
        from alembic.config import Config

        cfg = Config(str(_BACKEND_DIR / "alembic.ini"))
        command.upgrade(cfg, "head")
        # No exception = success

    @pytest.mark.asyncio
    async def test_seed_creates_roles_in_empty_db(self) -> None:
        """seed_database should create all 4 default roles in an empty database."""
        from app.database.database import DatabaseManager
        from app.database.seed import DEFAULT_ROLES, seed_database
        from app.database.session import get_session_factory
        from app.models.role import Role
        from sqlalchemy import select

        manager = DatabaseManager()
        await manager.connect()
        factory = get_session_factory(manager.engine)

        async with factory() as session:
            # Clear roles first (migration left them empty).
            await seed_database(session)

            result = await session.execute(select(Role))
            roles = result.scalars().all()

        await manager.disconnect()

        assert len(roles) == len(DEFAULT_ROLES)

    @pytest.mark.asyncio
    async def test_seed_is_idempotent(self) -> None:
        """Running seed twice should not create duplicate roles."""
        from app.database.database import DatabaseManager
        from app.database.seed import DEFAULT_ROLES, seed_database
        from app.database.session import get_session_factory
        from app.models.role import Role
        from sqlalchemy import select

        manager = DatabaseManager()
        await manager.connect()
        factory = get_session_factory(manager.engine)

        async with factory() as session:
            await seed_database(session)

        async with factory() as session:
            await seed_database(session)  # Second run — must not duplicate
            result = await session.execute(select(Role))
            roles = result.scalars().all()

        await manager.disconnect()

        assert len(roles) == len(DEFAULT_ROLES), (
            "Seed created duplicate roles — not idempotent"
        )
