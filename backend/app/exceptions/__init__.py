"""
Custom domain exception classes.

These are raised by service- and repository-layer code and are intended to be
caught by the handlers registered in ``app.core.exceptions``.

Add domain-specific exceptions here as the application grows.
"""

from __future__ import annotations


class AppBaseException(Exception):
    """Base class for all custom application exceptions."""

    def __init__(self, message: str = "An application error occurred.") -> None:
        self.message = message
        super().__init__(self.message)


class NotFoundError(AppBaseException):
    """Raised when a requested resource does not exist."""


class DomainValidationError(AppBaseException):
    """Raised when domain-level business-rule validation fails."""


class ServiceError(AppBaseException):
    """Raised when a service-layer operation fails."""
