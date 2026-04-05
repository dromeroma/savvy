"""App-specific FastAPI dependencies for checking app access and app-level roles."""

import uuid
from datetime import UTC, datetime
from typing import Any

from fastapi import Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, get_org_id
from src.core.exceptions import ForbiddenError
from src.modules.apps.models import AppRegistry, AppUserRole, OrganizationApp


def require_app(app_code: str):
    """Dependency factory that checks the organization has the given app active."""

    async def _check(
        request: Request,
        db: AsyncSession = Depends(get_db),
        org_id: uuid.UUID = Depends(get_org_id),
    ) -> OrganizationApp:
        stmt = (
            select(OrganizationApp)
            .join(AppRegistry, AppRegistry.id == OrganizationApp.app_id)
            .where(
                OrganizationApp.organization_id == org_id,
                AppRegistry.code == app_code,
                OrganizationApp.status.in_(["active", "trial"]),
            )
        )
        org_app = await db.scalar(stmt)
        if org_app is None:
            raise ForbiddenError(f"App '{app_code}' is not active for this organization.")

        # If trial, verify it has not expired.
        if org_app.status == "trial" and org_app.trial_ends_at is not None:
            if org_app.trial_ends_at < datetime.now(UTC):
                raise ForbiddenError(f"Trial for app '{app_code}' has expired.")

        request.state.current_app = org_app
        return org_app

    return _check


def require_app_role(app_code: str, *allowed_roles: str):
    """Dependency factory that checks the user has one of the allowed roles in this app."""

    async def _check(
        db: AsyncSession = Depends(get_db),
        org_id: uuid.UUID = Depends(get_org_id),
        user: dict[str, Any] = Depends(get_current_user),
    ) -> AppUserRole:
        user_id = uuid.UUID(user["sub"])

        stmt = (
            select(AppUserRole)
            .join(AppRegistry, AppRegistry.id == AppUserRole.app_id)
            .where(
                AppUserRole.organization_id == org_id,
                AppUserRole.user_id == user_id,
                AppRegistry.code == app_code,
            )
        )
        app_user_role = await db.scalar(stmt)
        if app_user_role is None or app_user_role.role not in allowed_roles:
            raise ForbiddenError(
                f"You do not have the required role in app '{app_code}'. "
                f"Required: {', '.join(allowed_roles)}."
            )
        return app_user_role

    return _check
