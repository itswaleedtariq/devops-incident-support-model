"""
HTTP request / response logging middleware.

Logs method, path, status code, and elapsed time for every request.
Injects ``X-Request-ID`` and ``X-Process-Time`` response headers.
"""

from __future__ import annotations

import time
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.logging import get_logger

logger = get_logger("middleware.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """Starlette middleware that logs every inbound HTTP request."""

    async def dispatch(self, request: Request, call_next) -> Response:  # type: ignore[override]
        request_id = uuid.uuid4().hex[:8]
        start = time.perf_counter()

        logger.info(
            "[%s] --> %s %s",
            request_id,
            request.method,
            request.url.path,
        )

        response: Response = await call_next(request)

        elapsed_ms = (time.perf_counter() - start) * 1000

        logger.info(
            "[%s] <-- %s %s | %d | %.2fms",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

        response.headers["X-Request-ID"] = request_id
        response.headers["X-Process-Time"] = f"{elapsed_ms:.2f}ms"

        return response
