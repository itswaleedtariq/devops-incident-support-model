"""
Security-headers middleware.

Adds hardening HTTP response headers on every response:

* ``X-Content-Type-Options: nosniff``
* ``X-Frame-Options: DENY``
* ``Referrer-Policy: strict-origin-when-cross-origin``
* ``Strict-Transport-Security`` (production only)
* ``Content-Security-Policy: default-src 'self'`` (baseline)
"""

from __future__ import annotations

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.config.settings import settings


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Attach standard security headers to every response."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        response: Response = await call_next(request)

        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault(
            "Referrer-Policy", "strict-origin-when-cross-origin"
        )
        response.headers.setdefault(
            "Permissions-Policy", "geolocation=(), microphone=(), camera=()"
        )

        # A minimal API-friendly CSP.  Adjust for embedded Swagger assets etc.
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; frame-ancestors 'none';",
        )

        if settings.APP_ENV == "production":
            response.headers.setdefault(
                "Strict-Transport-Security",
                "max-age=63072000; includeSubDomains; preload",
            )

        return response
