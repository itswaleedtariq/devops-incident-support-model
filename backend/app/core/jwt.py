"""
JWT encode/decode primitives.

Two token types are supported:

* **Access token** — short-lived (minutes); presented on every API request
  in the ``Authorization: Bearer …`` header.
* **Refresh token** — long-lived (days); used only to mint new access tokens.
  The token itself is stored server-side as a SHA-256 hash so it can be
  revoked before its natural expiry.

All tokens include:
    * ``sub`` — user ID (UUID string)
    * ``exp`` — expiry timestamp (int seconds since epoch)
    * ``iat`` — issued-at timestamp
    * ``type`` — ``"access"`` or ``"refresh"``
    * ``jti`` — unique token identifier (UUID)
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.config.settings import settings

ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


class JWTError(Exception):
    """Raised when a JWT cannot be decoded or validated."""


def _build_payload(
    subject: str,
    token_type: str,
    expires_delta: timedelta,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Assemble a base JWT payload with standard claims."""
    now = datetime.now(timezone.utc)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + expires_delta).timestamp()),
        "jti": uuid.uuid4().hex,
        "type": token_type,
    }
    if extra:
        payload.update(extra)
    return payload


def create_access_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """
    Encode a short-lived access token for *subject* (user UUID string).

    Args:
        subject:         The user identifier stored in ``sub``.
        expires_delta:   Override for the default access-token TTL.
        extra_claims:    Optional additional claims (e.g. role name).

    Returns:
        The signed, URL-safe JWT string.
    """
    delta = expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = _build_payload(subject, ACCESS_TOKEN_TYPE, delta, extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def create_refresh_token(
    subject: str,
    expires_delta: timedelta | None = None,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Encode a long-lived refresh token for *subject*."""
    delta = expires_delta or timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    payload = _build_payload(subject, REFRESH_TOKEN_TYPE, delta, extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def decode_token(token: str, expected_type: str | None = None) -> dict[str, Any]:
    """
    Decode and validate *token*.

    Args:
        token:         The raw JWT string.
        expected_type: If provided, raises when the token's ``type`` claim
                       does not match (e.g. reject a refresh token where an
                       access token was expected).

    Returns:
        The decoded payload as a dict.

    Raises:
        JWTError: If the token is malformed, expired, or of the wrong type.
    """
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise JWTError("Token has expired.") from exc
    except jwt.InvalidTokenError as exc:
        raise JWTError(f"Invalid token: {exc}") from exc

    if expected_type is not None and payload.get("type") != expected_type:
        raise JWTError(
            f"Token type mismatch: expected {expected_type!r}, "
            f"got {payload.get('type')!r}."
        )
    return payload
