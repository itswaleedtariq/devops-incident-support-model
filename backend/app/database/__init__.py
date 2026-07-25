"""
Database package.

Public surface:
    ``db_manager``  — application-wide :class:`DatabaseManager` singleton.
    ``Base``        — SQLAlchemy declarative base for all ORM models.
    ``get_db``      — FastAPI dependency that yields an ``AsyncSession``.
"""

from app.database.base import Base
from app.database.database import DatabaseManager, db_manager
from app.database.session import get_db

__all__ = ["Base", "DatabaseManager", "db_manager", "get_db"]
