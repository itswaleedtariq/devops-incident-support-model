"""
Configuration package.

Exposes ``settings`` and ``get_settings`` for convenient imports:

    from app.config import settings
"""

from app.config.settings import get_settings, settings

__all__ = ["get_settings", "settings"]
