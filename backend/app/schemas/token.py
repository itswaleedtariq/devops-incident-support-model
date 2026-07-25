"""
Token-related Pydantic schemas.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class TokenPair(BaseModel):
    """Access + refresh token pair returned on login and refresh."""

    access_token: str = Field(..., description="Short-lived JWT access token.")
    refresh_token: str = Field(..., description="Long-lived refresh token.")
    token_type: str = Field(default="bearer", description="Token scheme.")
    expires_in: int = Field(..., description="Access token lifetime in seconds.")


class RefreshTokenRequest(BaseModel):
    """Request body for the token-refresh endpoint."""

    refresh_token: str = Field(..., min_length=10, description="The refresh JWT.")


class TokenPayload(BaseModel):
    """Decoded payload from a validated JWT."""

    sub: str
    exp: int
    iat: int
    type: str
    jti: str
