"""
API v1 router.

Aggregates all v1 endpoint routers and exposes ``api_v1_router`` to be
mounted at ``/api/v1`` inside ``app.main.create_app``.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.endpoints.auth import router as auth_router
from app.api.v1.endpoints.health import router as health_router
from app.api.v1.endpoints.users import router as users_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(auth_router)
api_v1_router.include_router(users_router)
