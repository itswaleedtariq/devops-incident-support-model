"""
Centralised exception handlers for FastAPI.

Registered in ``app.main.create_app`` for:
- Starlette / FastAPI HTTP exceptions
- Pydantic request-validation errors
- Any unhandled Python exception (catch-all)
"""

from __future__ import annotations

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger
from app.schemas.response import StandardResponse

logger = get_logger("core.exceptions")


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    """Handle Starlette / FastAPI HTTP exceptions and return a standard envelope."""
    logger.warning(
        "HTTP %s on %s %s — %s",
        exc.status_code,
        request.method,
        request.url.path,
        exc.detail,
    )
    payload: StandardResponse[None] = StandardResponse(
        success=False,
        message=str(exc.detail),
        data=None,
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump())


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic request-validation errors (HTTP 422)."""
    errors = exc.errors()
    logger.warning(
        "Validation error on %s %s — %d error(s)",
        request.method,
        request.url.path,
        len(errors),
    )
    payload: StandardResponse[dict] = StandardResponse(
        success=False,
        message="Request validation failed.",
        data={"errors": errors},
    )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=payload.model_dump(),
    )


async def unhandled_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Catch-all handler for unexpected exceptions; logs the full traceback."""
    logger.exception(
        "Unhandled exception on %s %s",
        request.method,
        request.url.path,
    )
    payload: StandardResponse[None] = StandardResponse(
        success=False,
        message="An unexpected internal error occurred.",
        data=None,
    )
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=payload.model_dump(),
    )
