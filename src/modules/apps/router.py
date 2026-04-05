"""FastAPI router for app registry and app management endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, get_org_id, require_role
from src.modules.apps.schemas import (
    ActivateAppRequest,
    AppCatalogResponse,
    AppUserRoleResponse,
    AssignRoleRequest,
    MyAppResponse,
    OrganizationAppResponse,
)
from src.modules.apps.service import AppsService

router = APIRouter(prefix="/apps", tags=["Apps"])


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------


@router.get(
    "/catalog",
    response_model=list[AppCatalogResponse],
    dependencies=[Depends(get_current_user)],
)
async def get_catalog(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List all available apps in the Savvy ecosystem."""
    return await AppsService.get_catalog(db)


# ---------------------------------------------------------------------------
# My Apps
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=list[MyAppResponse],
)
async def get_my_apps(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    """List apps the current organization has, with the user's role in each."""
    user_id = uuid.UUID(user["sub"])
    return await AppsService.get_my_apps(db, org_id, user_id)


# ---------------------------------------------------------------------------
# Activate / Deactivate
# ---------------------------------------------------------------------------


@router.post(
    "/activate",
    response_model=OrganizationAppResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("owner"))],
)
async def activate_app(
    data: ActivateAppRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    """Activate an app for the organization (owner only)."""
    user_id = uuid.UUID(user["sub"])
    org_app = await AppsService.activate_app(db, org_id, data.app_code, user_id)

    # Enrich response with app details.
    from sqlalchemy import select
    from src.modules.apps.models import AppRegistry

    app = await db.scalar(select(AppRegistry).where(AppRegistry.id == org_app.app_id))
    return OrganizationAppResponse(
        id=org_app.id,
        app_code=app.code,
        app_name=app.name,
        status=org_app.status,
        activated_at=org_app.activated_at,
        trial_ends_at=org_app.trial_ends_at,
    )


@router.post(
    "/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("owner"))],
)
async def deactivate_app(
    data: ActivateAppRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    """Deactivate an app for the organization (owner only)."""
    await AppsService.deactivate_app(db, org_id, data.app_code)


# ---------------------------------------------------------------------------
# App Users / Roles
# ---------------------------------------------------------------------------


@router.get(
    "/{app_code}/users",
    response_model=list[AppUserRoleResponse],
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def get_app_users(
    app_code: str,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List users with roles for an app (admin+ only)."""
    return await AppsService.get_app_users(db, org_id, app_code)


@router.post(
    "/{app_code}/users/assign-role",
    response_model=AppUserRoleResponse,
    status_code=status.HTTP_200_OK,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def assign_role(
    app_code: str,
    data: AssignRoleRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Assign a role to a user in an app (admin+ only)."""
    return await AppsService.assign_role(db, org_id, app_code, data.user_id, data.role)


@router.delete(
    "/{app_code}/users/{user_id}/role",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def revoke_role(
    app_code: str,
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    """Revoke a user's role from an app (admin+ only)."""
    await AppsService.revoke_role(db, org_id, app_code, user_id)
