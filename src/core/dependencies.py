"""Reusable FastAPI dependencies for auth, database sessions, and org context."""

import uuid
from collections.abc import AsyncGenerator, Callable
from typing import Any

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.database import async_session_factory
from src.core.exceptions import ForbiddenError, UnauthorizedError
from src.core.security import verify_token

bearer_scheme = HTTPBearer(auto_error=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Yield an async database session, committing on success."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
) -> dict[str, Any]:
    """Extract and validate the JWT from the Authorization header."""
    if credentials is None:
        raise UnauthorizedError("Missing authentication token.")

    try:
        payload = verify_token(credentials.credentials)
    except JWTError:
        raise UnauthorizedError("Invalid or expired token.")

    if payload.get("type") != "access":
        raise UnauthorizedError("Invalid token type. Access token required.")

    sub: str | None = payload.get("sub")
    if sub is None:
        raise UnauthorizedError("Token payload missing subject.")

    # Propagate org_id into request state.
    org_id_raw = payload.get("org_id")
    if org_id_raw is not None:
        try:
            request.state.org_id = uuid.UUID(str(org_id_raw))
        except ValueError:
            request.state.org_id = None

    return payload


async def get_org_id(
    request: Request,
    _user: dict[str, Any] = Depends(get_current_user),
) -> uuid.UUID:
    """Return the resolved organization ID from the JWT."""
    org_id: uuid.UUID | None = getattr(request.state, "org_id", None)
    if org_id is None:
        raise ForbiddenError("No organization context found. Ensure your token includes an org_id.")
    return org_id


def require_role(*allowed_roles: str) -> Callable[..., Any]:
    """Dependency factory that verifies the user holds one of the allowed roles."""

    async def _check_role(
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        user_role: str | None = user.get("role")
        if user_role not in allowed_roles:
            raise ForbiddenError(
                f"Role '{user_role}' is not authorized. Required: {', '.join(allowed_roles)}."
            )
        return user

    return _check_role
