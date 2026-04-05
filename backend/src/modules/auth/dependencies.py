"""Auth-specific FastAPI dependencies.

Most authentication dependencies live in ``src.core.dependencies``.  This
module provides a convenient accessor for the :class:`AuthService` singleton
so that routers can declare it via ``Depends``.
"""

from __future__ import annotations

from src.modules.auth.service import AuthService, auth_service


def get_auth_service() -> AuthService:
    """Return the module-level AuthService instance."""
    return auth_service
