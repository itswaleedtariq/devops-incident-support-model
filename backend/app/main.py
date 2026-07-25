"""
Application entry point and factory.

Usage
-----
Development::

    uvicorn app.main:app --reload

Production::

    uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.api.v1.router import api_v1_router
from app.config.settings import settings
from app.core.exceptions import (
    http_exception_handler,
    unhandled_exception_handler,
    validation_exception_handler,
)
from app.core.logging import get_logger, setup_logging
from app.middleware.logging_middleware import RequestLoggingMiddleware
from app.schemas.response import RootData, StandardResponse


# ---------------------------------------------------------------------------
# Lifespan
# ---------------------------------------------------------------------------


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:  # noqa: ARG001
    """Application lifespan handler — runs startup / shutdown logic."""
    logger = get_logger("main")
    logger.info(
        "Starting %s v%s [env=%s]",
        settings.APP_NAME,
        settings.APP_VERSION,
        settings.APP_ENV,
    )
    yield
    logger.info("Shutting down %s.", settings.APP_NAME)


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def create_app() -> FastAPI:
    """
    Create and fully configure the FastAPI application instance.

    Using a factory pattern means tests can call ``create_app()`` independently
    without sharing global state between test sessions.

    Returns:
        A fully configured :class:`fastapi.FastAPI` instance.
    """
    # Initialise logging before anything else so all bootstrap messages appear.
    setup_logging(
        log_level=settings.LOG_LEVEL,
        log_dir=settings.LOG_DIR,
        log_file=settings.LOG_FILE,
        max_bytes=settings.LOG_MAX_BYTES,
        backup_count=settings.LOG_BACKUP_COUNT,
    )

    application = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=settings.APP_DESCRIPTION,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        debug=settings.DEBUG,
        lifespan=lifespan,
    )

    # ------------------------------------------------------------------
    # Middleware  (first added = outermost wrapper)
    # ------------------------------------------------------------------
    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # TODO(milestone-2): restrict to known frontend origins
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.add_middleware(RequestLoggingMiddleware)

    # ------------------------------------------------------------------
    # Exception handlers
    # ------------------------------------------------------------------
    application.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,  # type: ignore[arg-type]
    )
    application.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,  # type: ignore[arg-type]
    )
    application.add_exception_handler(
        Exception,
        unhandled_exception_handler,
    )

    # ------------------------------------------------------------------
    # Routers
    # ------------------------------------------------------------------
    application.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    # ------------------------------------------------------------------
    # Root endpoint
    # ------------------------------------------------------------------
    @application.get(
        "/",
        response_model=StandardResponse[RootData],
        summary="Root",
        description="Returns basic application information.",
        tags=["Root"],
    )
    async def root() -> StandardResponse[RootData]:
        """Return the application name and running status."""
        return StandardResponse(
            success=True,
            message="DevOps Incident Support Model is running.",
            data=RootData(
                application=settings.APP_NAME,
                status="running",
            ),
        )

    return application


# ---------------------------------------------------------------------------
# Module-level ``app`` instance consumed by Uvicorn
# ---------------------------------------------------------------------------

app: FastAPI = create_app()
