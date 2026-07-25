"""
Alembic migration environment.

This module is executed by every ``alembic`` CLI command.  It:

1. Loads application settings to obtain the database URL.
2. Imports ``Base.metadata`` and all ORM models so Alembic can detect changes.
3. Supports both *offline* (URL only) and *online* (live connection) modes.
4. Uses the async SQLAlchemy engine (asyncpg driver) with ``run_sync`` so
   migration functions run synchronously against the async engine without a
   separate sync driver dependency.

Run from the ``backend/`` directory:

    alembic current
    alembic upgrade head
    alembic downgrade -1
    alembic revision --autogenerate -m "describe the change"
"""

from __future__ import annotations

import asyncio
import logging
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Path setup — ensure ``backend/`` is on sys.path so ``app`` is importable
# ---------------------------------------------------------------------------
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# ---------------------------------------------------------------------------
# Application imports
# ---------------------------------------------------------------------------
from app.config.settings import settings  # noqa: E402
from app.database.base import Base  # noqa: E402

# Import every model module so their tables are registered with Base.metadata.
# Alembic's --autogenerate compares metadata against the live schema to detect
# new tables, dropped tables, added/removed columns, and index changes.
import app.models  # noqa: F401

# ---------------------------------------------------------------------------
# Alembic config object
# ---------------------------------------------------------------------------
config = context.config

# Override sqlalchemy.url from application settings (env vars / .env file).
# This ensures credentials are NEVER hard-coded in alembic.ini.
config.set_main_option("sqlalchemy.url", settings.async_database_url)

# Attach Python logging from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

logger = logging.getLogger("alembic.env")

# Target metadata object — Alembic compares this against the live schema.
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Shared migration options
# ---------------------------------------------------------------------------

# Options passed to context.configure() in both offline and online modes.
_MIGRATION_OPTIONS: dict = {
    "target_metadata": target_metadata,
    # Detect column type changes (e.g. VARCHAR(50) → VARCHAR(100)).
    "compare_type": True,
    # Detect changes to server defaults.
    "compare_server_default": True,
    # Include PostgreSQL schemas (leave as False for single-schema setups).
    "include_schemas": False,
}


# ---------------------------------------------------------------------------
# Offline migration mode
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """
    Run migrations without a live database connection.

    Generates plain SQL that can be inspected or applied manually:

        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        **_MIGRATION_OPTIONS,
    )
    logger.info("Running migrations in OFFLINE mode (SQL generation).")
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migration mode (async)
# ---------------------------------------------------------------------------


def do_run_migrations(connection: Connection) -> None:
    """Configure Alembic and run all pending migrations (sync context)."""
    context.configure(connection=connection, **_MIGRATION_OPTIONS)
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async engine and run migrations via ``connection.run_sync``.

    ``NullPool`` prevents connection reuse — each migration run gets a fresh
    connection and disposes it immediately on completion.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    logger.info("Connecting to database for migration.")
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()
    logger.info("Migration complete.")


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()


from __future__ import annotations

import asyncio
import sys
from logging.config import fileConfig
from pathlib import Path

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# ---------------------------------------------------------------------------
# Path setup — ensure ``backend/`` is on sys.path so ``app`` is importable
# ---------------------------------------------------------------------------
# alembic.ini sets ``prepend_sys_path = .`` (backend/), so this is
# typically a no-op, but we guard explicitly for safety.
_backend_dir = Path(__file__).resolve().parent.parent
if str(_backend_dir) not in sys.path:
    sys.path.insert(0, str(_backend_dir))

# ---------------------------------------------------------------------------
# Application imports
# ---------------------------------------------------------------------------
from app.config.settings import settings          # noqa: E402
from app.database.base import Base                # noqa: E402

# Import the models package so every table is registered with Base.metadata.
# Alembic's --autogenerate compares Base.metadata against the live schema
# to detect additions, removals, and column changes.
import app.models  # noqa: F401

# ---------------------------------------------------------------------------
# Alembic config object
# ---------------------------------------------------------------------------
config = context.config

# Set the database URL from application settings (overrides alembic.ini value).
config.set_main_option("sqlalchemy.url", settings.async_database_url)

# Attach Python logging configuration from alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Target metadata for --autogenerate support
target_metadata = Base.metadata


# ---------------------------------------------------------------------------
# Offline migration mode
# ---------------------------------------------------------------------------


def run_migrations_offline() -> None:
    """
    Run migrations without a live database connection.

    Useful for generating plain SQL scripts from migrations:

        alembic upgrade head --sql > migration.sql
    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


# ---------------------------------------------------------------------------
# Online migration mode (async)
# ---------------------------------------------------------------------------


def do_run_migrations(connection: Connection) -> None:
    """Execute pending migrations against *connection* (sync context)."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
        compare_server_default=True,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """
    Create an async engine and run migrations via ``run_sync``.

    ``NullPool`` is used so that the engine disposes immediately after
    the migration run without lingering pooled connections.
    """
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """Entry point for online migration mode."""
    asyncio.run(run_async_migrations())


# ---------------------------------------------------------------------------
# Dispatch
# ---------------------------------------------------------------------------

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
