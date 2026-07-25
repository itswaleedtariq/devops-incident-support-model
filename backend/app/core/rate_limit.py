"""
SlowAPI rate-limiter bootstrap.

Endpoints opt in by importing :data:`limiter` and decorating with
``@limiter.limit("<rate>")``.  ``main.py`` registers the limiter on the app
and installs the default handler that turns rate-limit exceptions into a
JSON response using the shared ``StandardResponse`` envelope.
"""

from __future__ import annotations

from fastapi import Request, status
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.logging import get_logger
from app.schemas.response import StandardResponse

logger = get_logger("core.rate_limit")

#: Application-wide SlowAPI limiter, keyed by client IP address.
#: Endpoints attach limits per-route with ``@limiter.limit("5/minute")``.
limiter = Limiter(key_func=get_remote_address)


async def rate_limit_exceeded_handler(
    request: Request, exc: RateLimitExceeded
) -> JSONResponse:
    """Return a standardised JSON response for HTTP 429 rate-limit errors."""
    logger.warning(
        "Rate limit exceeded from %s on %s %s",
        get_remote_address(request),
        request.method,
        request.url.path,
    )
    payload: StandardResponse[None] = StandardResponse(
        success=False,
        message=f"Rate limit exceeded: {exc.detail}",
        data=None,
    )
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        content=payload.model_dump(),
    )
