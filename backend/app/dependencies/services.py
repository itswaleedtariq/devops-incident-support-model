"""
Service dependency providers.

FastAPI ``Depends`` callables that assemble service objects from their
underlying repositories.
"""

from __future__ import annotations

from fastapi import Depends

from app.dependencies.repositories import (
    get_refresh_token_repository,
    get_role_repository,
    get_user_repository,
)
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository
from app.services.auth_service import AuthService
from app.services.token_service import TokenService
from app.services.user_service import UserService


def get_user_service(
    user_repo: UserRepository = Depends(get_user_repository),
) -> UserService:
    return UserService(user_repo)


def get_token_service(
    refresh_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
) -> TokenService:
    return TokenService(refresh_repo)


def get_auth_service(
    user_service: UserService = Depends(get_user_service),
    token_service: TokenService = Depends(get_token_service),
    role_repo: RoleRepository = Depends(get_role_repository),
) -> AuthService:
    return AuthService(
        user_service=user_service,
        token_service=token_service,
        role_repo=role_repo,
    )
