"""
Core package.

Exposes shared infrastructure utilities: logging and exception handlers.
"""

from app.core.logging import get_logger, setup_logging

__all__ = ["get_logger", "setup_logging"]
