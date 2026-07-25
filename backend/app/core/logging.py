"""
Centralised logging configuration.

Call ``setup_logging()`` once at application startup (inside the app factory).
Use ``get_logger(name)`` everywhere else to obtain a child logger.
"""

from __future__ import annotations

import logging
import logging.handlers
from pathlib import Path

_LOG_FORMAT = "%(asctime)s | %(levelname)-8s | %(name)-40s | %(message)s"
_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    log_level: str = "INFO",
    log_dir: str = "logs",
    log_file: str = "app.log",
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
) -> logging.Logger:
    """
    Configure the application root logger with console and rotating-file handlers.

    Args:
        log_level:    Minimum severity (DEBUG / INFO / WARNING / ERROR / CRITICAL).
        log_dir:      Directory where log files are stored (created if absent).
        log_file:     Name of the rotating log file.
        max_bytes:    File size threshold before rotation.
        backup_count: Number of backup files to retain.

    Returns:
        The configured root ``logging.Logger`` for the application.
    """
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    log_path = Path(log_dir)
    log_path.mkdir(parents=True, exist_ok=True)

    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    # Console handler -------------------------------------------------------
    console_handler = logging.StreamHandler()
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)

    # Rotating file handler -------------------------------------------------
    file_handler = logging.handlers.RotatingFileHandler(
        log_path / log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(numeric_level)
    file_handler.setFormatter(formatter)

    root = logging.getLogger("devops_incident")
    root.setLevel(numeric_level)

    # Guard against duplicate handlers added by Uvicorn --reload
    if not root.handlers:
        root.addHandler(console_handler)
        root.addHandler(file_handler)

    return root


def get_logger(name: str) -> logging.Logger:
    """
    Return a child logger under the application namespace.

    Args:
        name: Component identifier, e.g. ``"api.v1.health"`` or ``"core.exceptions"``.

    Returns:
        A ``logging.Logger`` parented to ``devops_incident``.
    """
    return logging.getLogger(f"devops_incident.{name}")
