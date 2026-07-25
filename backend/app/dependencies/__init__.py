"""
Dependencies package.

Public re-exports for FastAPI ``Depends`` callables.
"""

from app.dependencies.current_user import (
    get_current_active_user,
    get_current_admin,
    get_current_user,
    require_permission,
)
from app.dependencies.database import get_db
from app.dependencies.services import (
    get_auth_service,
    get_token_service,
    get_user_service,
)

__all__ = [
    "get_db",
    "get_current_user",
    "get_current_active_user",
    "get_current_admin",
    "require_permission",
    "get_auth_service",
    "get_token_service",
    "get_user_service",
]
