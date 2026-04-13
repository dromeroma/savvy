"""Per-app permission-check dependency.

Every endpoint that wants fine-grained access control declares:

    @router.post("/sales", dependencies=[Depends(require_permission("pos", "sales.create"))])
    async def create_sale(...): ...

Resolution order for a request:

1. Read `sub` (user_id) and `org_id` from the JWT (via get_current_user).
2. If the user has an active `super_admin` platform role → allow (super admins
   shouldn't hit app endpoints anyway, but never block them if they do).
3. Look up the user's `membership.role`. If it's 'owner' → allow
   (top-level org owners bypass per-app permission checks).
4. Look up `app_user_roles` for (user, org, app_code). If missing → 403.
5. Resolve that role in `app_role_catalog` (system OR org-scoped custom)
   and check whether any of the required permission codes are present.
6. Cache the resolved permission set on `request.state` so multiple
   `require_permission` calls in the same request don't re-query.
"""

from __future__ import annotations

import uuid
from collections.abc import Callable
from typing import Any

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, get_org_id
from src.core.exceptions import ForbiddenError
from src.modules.apps.models import AppRegistry, AppUserRole
from src.modules.organization.models import Membership
from src.modules.platform.models import AppRoleCatalog


async def _resolve_permissions(
    db: AsyncSession,
    request: Request,
    user_id: uuid.UUID,
    org_id: uuid.UUID,
    app_code: str,
) -> set[str] | None:
    """Return the set of permission codes granted to the user for the app.

    Returns None when the user has **unrestricted** access (org owner or
    super admin) — callers should treat `None` as "allow everything".
    Returns an empty set when the user has no app role at all — callers
    should treat an empty set as "deny".
    """
    # Request-level memoization
    cache: dict[str, set[str] | None] = getattr(request.state, "_perm_cache", {})
    if not cache:
        request.state._perm_cache = cache
    key = f"{app_code}:{user_id}:{org_id}"
    if key in cache:
        return cache[key]

    # Membership role (org-level): owners bypass everything
    membership = await db.scalar(
        select(Membership).where(
            Membership.organization_id == org_id,
            Membership.user_id == user_id,
        )
    )
    if membership is not None and membership.role == "owner":
        cache[key] = None
        return None

    # Find the app
    app = await db.scalar(
        select(AppRegistry).where(AppRegistry.code == app_code)
    )
    if app is None:
        cache[key] = set()
        return set()

    # Find the user's role in this app
    app_role_row = await db.scalar(
        select(AppUserRole).where(
            AppUserRole.organization_id == org_id,
            AppUserRole.user_id == user_id,
            AppUserRole.app_id == app.id,
        )
    )
    if app_role_row is None:
        cache[key] = set()
        return set()

    # Find the catalog entry (system role OR org-scoped custom role)
    catalog = await db.scalar(
        select(AppRoleCatalog).where(
            AppRoleCatalog.app_code == app_code,
            AppRoleCatalog.code == app_role_row.role,
            AppRoleCatalog.is_active.is_(True),
            (AppRoleCatalog.organization_id.is_(None))
            | (AppRoleCatalog.organization_id == org_id),
        )
    )
    if catalog is None:
        cache[key] = set()
        return set()

    # Owner-like app role: if the catalog entry code is 'owner' treat as unrestricted.
    if catalog.code == "owner":
        cache[key] = None
        return None

    perms = set(catalog.permissions or [])
    cache[key] = perms
    return perms


def require_permission(app_code: str, *required: str) -> Callable[..., Any]:
    """Dependency factory: require any one of `required` permission codes.

    Usage:
        @router.post(
            "/sales",
            dependencies=[Depends(require_permission("pos", "sales.create"))],
        )
    """

    async def _check(
        request: Request,
        user: dict[str, Any] = Depends(get_current_user),
        org_id: uuid.UUID = Depends(get_org_id),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        # Super admin bypass (defensive — super admins normally don't enter orgs)
        platform_roles = user.get("platform_roles") or []
        if isinstance(platform_roles, list) and "super_admin" in platform_roles:
            return

        user_id = uuid.UUID(user["sub"])
        perms = await _resolve_permissions(db, request, user_id, org_id, app_code)
        if perms is None:  # unrestricted (org owner or app 'owner' role)
            return
        if not any(p in perms for p in required):
            raise ForbiddenError(
                f"Missing required permission for {app_code}: any of "
                f"{', '.join(required)}.",
            )

    return _check
