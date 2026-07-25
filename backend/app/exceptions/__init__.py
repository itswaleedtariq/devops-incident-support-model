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


class DuplicateResourceError(AppBaseException):
    """Raised when creating a resource that already exists (unique constraint)."""


class InvalidCredentialsError(AppBaseException):
    """Raised when login credentials do not match a stored user."""


class InactiveUserError(AppBaseException):
    """Raised when authentication succeeds but the user account is disabled."""


class InvalidTokenError(AppBaseException):
    """Raised when a supplied token is malformed, expired, or revoked."""


class PermissionDeniedError(AppBaseException):
    """Raised when a user lacks the required permission for an operation."""


class WeakPasswordError(AppBaseException):
    """Raised when a supplied password fails the strength policy."""

