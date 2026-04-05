"""Organization-specific FastAPI dependencies."""

from typing import Any

from fastapi import Depends

from src.core.dependencies import get_current_user


async def get_current_user_role(
    user: dict[str, Any] = Depends(get_current_user),
) -> str:
    """Extract the role claim from the authenticated user's JWT payload."""
    return user.get("role", "member")


async def get_current_user_id(
    user: dict[str, Any] = Depends(get_current_user),
) -> str:
    """Extract the user id (sub) from the authenticated user's JWT payload."""
    return user["sub"]
