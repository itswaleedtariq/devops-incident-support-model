"""
Password service.

Thin business-logic wrapper around the pure hashing utilities in
``app.core.security``.  Adds password-policy enforcement via the Pydantic
validators (which raise :class:`ValueError` in ``UserCreate``); the service
exposes the same rules as a callable for non-Pydantic code paths.
"""

from __future__ import annotations

import re

from app.config.settings import settings
from app.core.security import hash_password, needs_rehash, verify_password
from app.exceptions import WeakPasswordError

_SPECIAL_RE = re.compile(r"[!@#$%^&*()_+\-=\[\]{};:'\",.<>/?\\|`~]")


class PasswordService:
    """Password hashing and validation logic."""

    @staticmethod
    def hash(plain: str) -> str:
        """Return the bcrypt hash of *plain*."""
        return hash_password(plain)

    @staticmethod
    def verify(plain: str, hashed: str) -> bool:
        """Return ``True`` if *plain* matches *hashed*."""
        return verify_password(plain, hashed)

    @staticmethod
    def needs_rehash(hashed: str) -> bool:
        """Return ``True`` if *hashed* uses an outdated scheme/work factor."""
        return needs_rehash(hashed)

    @staticmethod
    def validate_strength(plain: str) -> None:
        """
        Enforce the configured password policy.

        Raises:
            WeakPasswordError: When *plain* fails any active rule.
        """
        errors: list[str] = []
        if len(plain) < settings.PASSWORD_MIN_LENGTH:
            errors.append(f"minimum {settings.PASSWORD_MIN_LENGTH} characters")
        if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", plain):
            errors.append("one uppercase letter")
        if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", plain):
            errors.append("one lowercase letter")
        if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", plain):
            errors.append("one digit")
        if settings.PASSWORD_REQUIRE_SPECIAL and not _SPECIAL_RE.search(plain):
            errors.append("one special character")
        if errors:
            raise WeakPasswordError(
                "Password does not meet policy: requires " + ", ".join(errors) + "."
            )
