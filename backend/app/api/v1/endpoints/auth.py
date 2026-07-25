"""
Authentication endpoints.

Routes:
    POST   /api/v1/auth/register         Create a new user.
    POST   /api/v1/auth/login            Exchange credentials for a token pair.
    POST   /api/v1/auth/logout           Revoke a refresh token.
    POST   /api/v1/auth/refresh          Rotate a refresh token.
    POST   /api/v1/auth/change-password  Update the current user's password.
    POST   /api/v1/auth/forgot-password  Trigger password-reset flow (stub).
    POST   /api/v1/auth/reset-password   Complete password reset (stub).
    GET    /api/v1/auth/me               Return the current user.

Rate-limited routes use the SlowAPI ``@limiter.limit`` decorator.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.config.settings import settings
from app.core.rate_limit import limiter
from app.dependencies.current_user import get_current_active_user
from app.dependencies.services import get_auth_service
from app.exceptions import (
    DuplicateResourceError,
    InactiveUserError,
    InvalidCredentialsError,
    InvalidTokenError,
    NotFoundError,
    WeakPasswordError,
)
from app.models.user import User
from app.schemas.auth import (
    ChangePasswordRequest,
    ForgotPasswordRequest,
    LoginRequest,
    ResetPasswordRequest,
)
from app.schemas.response import StandardResponse
from app.schemas.token import RefreshTokenRequest, TokenPair
from app.schemas.user import UserCreate, UserRead
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


def _to_user_read(user: User) -> UserRead:
    """Build a UserRead safely including the joined role name."""
    return UserRead(
        id=user.id,
        full_name=user.full_name,
        username=user.username,
        email=user.email,
        is_active=user.is_active,
        is_verified=user.is_verified,
        role_id=user.role_id,
        role_name=user.role.name if user.role is not None else None,
        created_at=user.created_at,
        updated_at=user.updated_at,
    )


# ---------------------------------------------------------------------------
# POST /register
# ---------------------------------------------------------------------------


@router.post(
    "/register",
    response_model=StandardResponse[UserRead],
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
)
@limiter.limit(settings.RATE_LIMIT_REGISTER)
async def register(
    request: Request,  # required by slowapi
    payload: UserCreate,
    auth_service: AuthService = Depends(get_auth_service),
) -> StandardResponse[UserRead]:
    """Create a new user account and assign the default ``Viewer`` role."""
    try:
        user = await auth_service.register(payload)
    except DuplicateResourceError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    except WeakPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return StandardResponse(
        success=True,
        message="User registered successfully.",
        data=_to_user_read(user),
    )


# ---------------------------------------------------------------------------
# POST /login
# ---------------------------------------------------------------------------


@router.post(
    "/login",
    response_model=StandardResponse[TokenPair],
    summary="Log in with email and password",
)
@limiter.limit(settings.RATE_LIMIT_LOGIN)
async def login(
    request: Request,
    payload: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> StandardResponse[TokenPair]:
    """Exchange credentials for an access + refresh token pair."""
    try:
        _user, tokens = await auth_service.login(str(payload.email), payload.password)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc

    return StandardResponse(
        success=True, message="Login successful.", data=tokens
    )


# ---------------------------------------------------------------------------
# POST /logout
# ---------------------------------------------------------------------------


@router.post(
    "/logout",
    response_model=StandardResponse[None],
    summary="Log out (revoke a refresh token)",
)
async def logout(
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> StandardResponse[None]:
    """Revoke the supplied refresh token."""
    await auth_service.logout(payload.refresh_token)
    return StandardResponse(success=True, message="Logged out.", data=None)


# ---------------------------------------------------------------------------
# POST /refresh
# ---------------------------------------------------------------------------


@router.post(
    "/refresh",
    response_model=StandardResponse[TokenPair],
    summary="Rotate a refresh token into a fresh token pair",
)
@limiter.limit(settings.RATE_LIMIT_REFRESH)
async def refresh(
    request: Request,
    payload: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> StandardResponse[TokenPair]:
    """Exchange a valid refresh token for a new access + refresh pair."""
    try:
        _user, tokens = await auth_service.refresh(payload.refresh_token)
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    except InactiveUserError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)
        ) from exc
    except NotFoundError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc

    return StandardResponse(
        success=True, message="Token refreshed.", data=tokens
    )


# ---------------------------------------------------------------------------
# POST /change-password
# ---------------------------------------------------------------------------


@router.post(
    "/change-password",
    response_model=StandardResponse[None],
    summary="Change the current user's password",
)
async def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(get_current_active_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> StandardResponse[None]:
    """Update the authenticated user's password and revoke existing sessions."""
    try:
        await auth_service.change_password(
            current_user, payload.current_password, payload.new_password
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc)
        ) from exc
    except WeakPasswordError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc)
        ) from exc

    return StandardResponse(
        success=True,
        message="Password updated. All other sessions were logged out.",
        data=None,
    )


# ---------------------------------------------------------------------------
# POST /forgot-password  (stub — email delivery in a future milestone)
# ---------------------------------------------------------------------------


@router.post(
    "/forgot-password",
    response_model=StandardResponse[None],
    summary="Trigger the password-reset flow (stub)",
)
@limiter.limit(settings.RATE_LIMIT_FORGOT_PASSWORD)
async def forgot_password(
    request: Request,
    payload: ForgotPasswordRequest,  # noqa: ARG001 — reserved for future use
) -> StandardResponse[None]:
    """
    Placeholder — always returns success to avoid revealing email existence.

    Email delivery and reset-token issuance land in a future milestone.
    """
    return StandardResponse(
        success=True,
        message=(
            "If an account with that email exists, a reset link has been sent."
        ),
        data=None,
    )


# ---------------------------------------------------------------------------
# POST /reset-password  (stub)
# ---------------------------------------------------------------------------


@router.post(
    "/reset-password",
    response_model=StandardResponse[None],
    summary="Complete password reset (stub)",
)
@limiter.limit(settings.RATE_LIMIT_RESET_PASSWORD)
async def reset_password(
    request: Request,
    payload: ResetPasswordRequest,  # noqa: ARG001 — reserved for future use
) -> StandardResponse[None]:
    """Placeholder — full implementation ships with the email flow."""
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password-reset flow is not implemented yet.",
    )


# ---------------------------------------------------------------------------
# GET /me
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=StandardResponse[UserRead],
    summary="Return the currently authenticated user",
)
async def me(
    current_user: User = Depends(get_current_active_user),
) -> StandardResponse[UserRead]:
    """Return the profile of the authenticated user."""
    return StandardResponse(
        success=True, message="OK.", data=_to_user_read(current_user)
    )
