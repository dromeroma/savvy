"""Business logic for app registry, organization apps, and app user roles."""

import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from src.modules.apps.models import AppRegistry, AppUserRole, OrganizationApp
from src.modules.apps.schemas import (
    AppCatalogResponse,
    AppUserRoleResponse,
    MyAppResponse,
)
from src.modules.apps.seed import APP_OWNER_ROLE


class AppsService:
    """Stateless service layer for app registry operations."""

    # ------------------------------------------------------------------
    # Catalog
    # ------------------------------------------------------------------

    @staticmethod
    async def get_catalog(db: AsyncSession) -> list[AppRegistry]:
        """Return all active apps in the catalog."""
        result = await db.execute(
            select(AppRegistry).where(AppRegistry.is_active.is_(True)).order_by(AppRegistry.name)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # My Apps
    # ------------------------------------------------------------------

    @staticmethod
    async def get_my_apps(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[MyAppResponse]:
        """Return apps the organization has, enriched with the user's role in each."""
        stmt = (
            select(OrganizationApp, AppRegistry, AppUserRole.role)
            .join(AppRegistry, AppRegistry.id == OrganizationApp.app_id)
            .outerjoin(
                AppUserRole,
                (AppUserRole.app_id == OrganizationApp.app_id)
                & (AppUserRole.organization_id == OrganizationApp.organization_id)
                & (AppUserRole.user_id == user_id),
            )
            .where(
                OrganizationApp.organization_id == org_id,
                OrganizationApp.status.in_(["active", "trial"]),
            )
            .order_by(AppRegistry.name)
        )
        result = await db.execute(stmt)
        rows = result.all()

        return [
            MyAppResponse(
                app=AppCatalogResponse.model_validate(app_reg),
                role=role,
                status=org_app.status,
                activated_at=org_app.activated_at,
                trial_ends_at=org_app.trial_ends_at,
                expires_at=org_app.expires_at,
            )
            for org_app, app_reg, role in rows
        ]

    # ------------------------------------------------------------------
    # Activate / Deactivate
    # ------------------------------------------------------------------

    @staticmethod
    async def activate_app(
        db: AsyncSession,
        org_id: uuid.UUID,
        app_code: str,
        activated_by_user_id: uuid.UUID,
    ) -> OrganizationApp:
        """Activate an app for the organization with a 14-day trial."""
        # Find the app by code.
        app = await db.scalar(
            select(AppRegistry).where(AppRegistry.code == app_code, AppRegistry.is_active.is_(True))
        )
        if app is None:
            raise NotFoundError(f"App '{app_code}' not found or is not active.")

        # Check not already active.
        existing = await db.scalar(
            select(OrganizationApp).where(
                OrganizationApp.organization_id == org_id,
                OrganizationApp.app_id == app.id,
                OrganizationApp.status.in_(["active", "trial"]),
            )
        )
        if existing is not None:
            raise ConflictError(f"App '{app_code}' is already active for this organization.")

        now = datetime.now(UTC)
        org_app = OrganizationApp(
            organization_id=org_id,
            app_id=app.id,
            status="trial",
            activated_at=now,
            trial_ends_at=now + timedelta(days=14),
        )
        db.add(org_app)
        await db.flush()

        # Auto-assign the activating user as the first role.
        owner_role = APP_OWNER_ROLE.get(app_code, "admin")
        app_user_role = AppUserRole(
            organization_id=org_id,
            user_id=activated_by_user_id,
            app_id=app.id,
            role=owner_role,
        )
        db.add(app_user_role)
        await db.flush()
        await db.refresh(org_app)
        return org_app

    @staticmethod
    async def deactivate_app(
        db: AsyncSession,
        org_id: uuid.UUID,
        app_code: str,
    ) -> None:
        """Set the app status to 'cancelled' for the organization."""
        app = await db.scalar(
            select(AppRegistry).where(AppRegistry.code == app_code)
        )
        if app is None:
            raise NotFoundError(f"App '{app_code}' not found.")

        org_app = await db.scalar(
            select(OrganizationApp).where(
                OrganizationApp.organization_id == org_id,
                OrganizationApp.app_id == app.id,
                OrganizationApp.status.in_(["active", "trial"]),
            )
        )
        if org_app is None:
            raise NotFoundError(f"App '{app_code}' is not active for this organization.")

        org_app.status = "cancelled"
        await db.flush()

    # ------------------------------------------------------------------
    # App Users / Roles
    # ------------------------------------------------------------------

    @staticmethod
    async def get_app_users(
        db: AsyncSession,
        org_id: uuid.UUID,
        app_code: str,
    ) -> list[AppUserRoleResponse]:
        """List all users with roles for an app within the organization."""
        app = await db.scalar(
            select(AppRegistry).where(AppRegistry.code == app_code)
        )
        if app is None:
            raise NotFoundError(f"App '{app_code}' not found.")

        result = await db.execute(
            select(AppUserRole).where(
                AppUserRole.organization_id == org_id,
                AppUserRole.app_id == app.id,
            ).order_by(AppUserRole.created_at)
        )
        roles = result.scalars().all()
        return [AppUserRoleResponse.model_validate(r) for r in roles]

    @staticmethod
    async def assign_role(
        db: AsyncSession,
        org_id: uuid.UUID,
        app_code: str,
        user_id: uuid.UUID,
        role: str,
    ) -> AppUserRole:
        """Assign or update a user's role in an app. Validates membership and app subscription."""
        from src.modules.organization.models import Membership

        # Check user is a member of the org.
        membership = await db.scalar(
            select(Membership).where(
                Membership.organization_id == org_id,
                Membership.user_id == user_id,
            )
        )
        if membership is None:
            raise ForbiddenError("User is not a member of this organization.")

        # Check org has this app active.
        app = await db.scalar(
            select(AppRegistry).where(AppRegistry.code == app_code)
        )
        if app is None:
            raise NotFoundError(f"App '{app_code}' not found.")

        org_app = await db.scalar(
            select(OrganizationApp).where(
                OrganizationApp.organization_id == org_id,
                OrganizationApp.app_id == app.id,
                OrganizationApp.status.in_(["active", "trial"]),
            )
        )
        if org_app is None:
            raise ForbiddenError(f"App '{app_code}' is not active for this organization.")

        # Create or update.
        existing = await db.scalar(
            select(AppUserRole).where(
                AppUserRole.organization_id == org_id,
                AppUserRole.user_id == user_id,
                AppUserRole.app_id == app.id,
            )
        )
        if existing is not None:
            existing.role = role
            await db.flush()
            await db.refresh(existing)
            return existing

        app_user_role = AppUserRole(
            organization_id=org_id,
            user_id=user_id,
            app_id=app.id,
            role=role,
        )
        db.add(app_user_role)
        await db.flush()
        await db.refresh(app_user_role)
        return app_user_role

    @staticmethod
    async def revoke_role(
        db: AsyncSession,
        org_id: uuid.UUID,
        app_code: str,
        user_id: uuid.UUID,
    ) -> None:
        """Remove a user's role from an app."""
        app = await db.scalar(
            select(AppRegistry).where(AppRegistry.code == app_code)
        )
        if app is None:
            raise NotFoundError(f"App '{app_code}' not found.")

        app_user_role = await db.scalar(
            select(AppUserRole).where(
                AppUserRole.organization_id == org_id,
                AppUserRole.user_id == user_id,
                AppUserRole.app_id == app.id,
            )
        )
        if app_user_role is None:
            raise NotFoundError("User does not have a role in this app.")

        await db.delete(app_user_role)
        await db.flush()
