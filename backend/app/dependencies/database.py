"""
Database dependency re-export.

FastAPI endpoints depend on this module rather than reaching into
``app.database.session`` directly.
"""

from app.database.session import get_db

__all__ = ["get_db"]
