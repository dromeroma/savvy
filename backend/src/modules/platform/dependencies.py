"""Platform-level auth dependencies.

These verify the caller holds one of the required platform roles and
short-circuit the request with ForbiddenError otherwise.

The platform_roles claim is populated at login time from
`user_platform_roles`, so role checks are zero-DB-cost per request.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from fastapi import Depends

from src.core.dependencies import get_current_user
from src.core.exceptions import ForbiddenError


async def get_platform_roles(
    user: dict[str, Any] = Depends(get_current_user),
) -> list[str]:
    """Return the caller's active platform roles (from the JWT claim)."""
    roles = user.get("platform_roles") or []
    if not isinstance(roles, list):
        return []
    return [str(r) for r in roles]


def require_platform_role(*allowed: str) -> Callable[..., Any]:
    """Factory: require at least one of the given platform roles."""

    async def _check(
        roles: list[str] = Depends(get_platform_roles),
        user: dict[str, Any] = Depends(get_current_user),
    ) -> dict[str, Any]:
        if not any(r in roles for r in allowed):
            raise ForbiddenError(
                f"This action requires one of the platform roles: {', '.join(allowed)}.",
            )
        return user

    return _check


async def require_super_admin(
    user: dict[str, Any] = Depends(get_current_user),
    roles: list[str] = Depends(get_platform_roles),
) -> dict[str, Any]:
    """Shortcut for the most common case: super_admin only."""
    if "super_admin" not in roles:
        raise ForbiddenError("This action requires platform role 'super_admin'.")
    return user
