"""
User-related Pydantic schemas.
"""

from __future__ import annotations

import re
import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

from app.config.settings import settings

# ---------------------------------------------------------------------------
# Username / password validators (reused across schemas)
# ---------------------------------------------------------------------------

_USERNAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{3,100}$")


def _validate_username(value: str) -> str:
    if not _USERNAME_RE.match(value):
        raise ValueError(
            "Username must be 3–100 chars, alphanumeric plus '.', '_' or '-'."
        )
    return value.lower()


def _validate_password_strength(value: str) -> str:
    """Enforce the configured password policy."""
    if len(value) < settings.PASSWORD_MIN_LENGTH:
        raise ValueError(
            f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters."
        )
    if settings.PASSWORD_REQUIRE_UPPERCASE and not re.search(r"[A-Z]", value):
        raise ValueError("Password must contain at least one uppercase letter.")
    if settings.PASSWORD_REQUIRE_LOWERCASE and not re.search(r"[a-z]", value):
        raise ValueError("Password must contain at least one lowercase letter.")
    if settings.PASSWORD_REQUIRE_DIGIT and not re.search(r"\d", value):
        raise ValueError("Password must contain at least one digit.")
    if settings.PASSWORD_REQUIRE_SPECIAL and not re.search(
        r"[!@#$%^&*()_+\-=\[\]{};:'\",.<>/?\\|`~]", value
    ):
        raise ValueError("Password must contain at least one special character.")
    return value


# ---------------------------------------------------------------------------
# Base
# ---------------------------------------------------------------------------


class UserBase(BaseModel):
    """Fields common to all user representations."""

    full_name: str = Field(..., min_length=1, max_length=200)
    username: str = Field(..., min_length=3, max_length=100)
    email: EmailStr

    @field_validator("username")
    @classmethod
    def _username_ok(cls, v: str) -> str:
        return _validate_username(v)


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------


class UserCreate(UserBase):
    """Payload for creating a user (admin) or registering."""

    password: str = Field(..., min_length=8, max_length=128)
    role_id: uuid.UUID | None = None

    @field_validator("password")
    @classmethod
    def _password_ok(cls, v: str) -> str:
        return _validate_password_strength(v)


class UserUpdate(BaseModel):
    """Partial update — every field optional."""

    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None
    is_active: bool | None = None
    is_verified: bool | None = None
    role_id: uuid.UUID | None = None


class UserSelfUpdate(BaseModel):
    """Fields a user is allowed to update on their own profile."""

    full_name: str | None = Field(default=None, min_length=1, max_length=200)
    email: EmailStr | None = None


# ---------------------------------------------------------------------------
# Read
# ---------------------------------------------------------------------------


class UserRead(BaseModel):
    """Public representation of a user."""

    id: uuid.UUID
    full_name: str
    username: str
    email: EmailStr
    is_active: bool
    is_verified: bool
    role_id: uuid.UUID | None
    role_name: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
