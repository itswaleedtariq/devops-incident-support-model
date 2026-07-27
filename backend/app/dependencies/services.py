"""Service dependency providers with lazy service imports."""

from __future__ import annotations

from fastapi import Depends

from app.dependencies.repositories import (
    get_incident_repository,
    get_refresh_token_repository,
    get_role_repository,
    get_user_repository,
)
from app.repositories.incident_repository import IncidentRepository
from app.repositories.refresh_token_repository import RefreshTokenRepository
from app.repositories.role_repository import RoleRepository
from app.repositories.user_repository import UserRepository


def get_user_service(user_repo: UserRepository = Depends(get_user_repository)):
    from app.services.user_service import UserService
    return UserService(user_repo)


def get_token_service(
    refresh_repo: RefreshTokenRepository = Depends(get_refresh_token_repository),
):
    from app.services.token_service import TokenService
    return TokenService(refresh_repo)


def get_auth_service(
    user_service=Depends(get_user_service),
    token_service=Depends(get_token_service),
    role_repo: RoleRepository = Depends(get_role_repository),
):
    from app.services.auth_service import AuthService
    return AuthService(
        user_service=user_service,
        token_service=token_service,
        role_repo=role_repo,
    )


def get_incident_service(
    incident_repo: IncidentRepository = Depends(get_incident_repository),
):
    from app.services.incident_service import IncidentService
    return IncidentService(incident_repo)
