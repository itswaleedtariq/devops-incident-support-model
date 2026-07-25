"""
Auth-related Pydantic request schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, EmailStr, Field, field_validator

from app.schemas.user import _validate_password_strength


class LoginRequest(BaseModel):
    """Credentials submitted to ``POST /api/v1/auth/login``."""

    email: EmailStr
    password: str = Field(..., min_length=1, max_length=128)


class ChangePasswordRequest(BaseModel):
    """Body for ``POST /api/v1/auth/change-password``."""

    current_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _new_password_ok(cls, v: str) -> str:
        return _validate_password_strength(v)


class ForgotPasswordRequest(BaseModel):
    """Body for ``POST /api/v1/auth/forgot-password``."""

    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Body for ``POST /api/v1/auth/reset-password``."""

    reset_token: str = Field(..., min_length=10)
    new_password: str = Field(..., min_length=8, max_length=128)

    @field_validator("new_password")
    @classmethod
    def _new_password_ok(cls, v: str) -> str:
        return _validate_password_strength(v)
