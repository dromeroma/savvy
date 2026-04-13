"""Business logic for the platform module.

All side-effectful actions (grant role, change plan, edit org, etc.)
MUST call `write_audit` so the action is traceable.
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from fastapi import Request
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.core.security import hash_password
from src.modules.apps.models import AppRegistry, AppUserRole, OrganizationApp
from src.modules.auth.models import User
from src.modules.organization.models import Membership, Organization
from src.modules.platform.models import (
    AppRoleCatalog,
    OrganizationFeatureOverride,
    OrganizationSubscription,
    PlanFeature,
    PlatformAuditLog,
    PlatformFeature,
    PlatformRole,
    SubscriptionPlan,
    UserPlatformRole,
)
from src.modules.platform.schemas import (
    AssignAppRoleRequest,
    FeatureCreate,
    InviteMemberRequest,
    OrgAppActivateRequest,
    OverrideSet,
    PlanCreate,
    PlanFeatureSet,
    PlanUpdate,
    PlatformOrgCreate,
    PlatformOrgUpdate,
    SubscriptionCreate,
    SubscriptionUpdate,
)


# =====================================================================
# Audit helper
# =====================================================================


async def write_audit(
    db: AsyncSession,
    actor_user_id: uuid.UUID,
    action: str,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    target_org_id: uuid.UUID | None = None,
    payload: dict[str, Any] | None = None,
    request: Request | None = None,
) -> PlatformAuditLog:
    """Append a row to platform_audit_log."""
    ip = None
    ua = None
    if request is not None:
        ip = request.headers.get("x-forwarded-for") or (
            request.client.host if request.client else None
        )
        ua = request.headers.get("user-agent")

    entry = PlatformAuditLog(
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        target_org_id=target_org_id,
        payload=payload,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(entry)
    await db.flush()
    return entry


# =====================================================================
# Helpers
# =====================================================================


async def _get_user_platform_role_codes(
    db: AsyncSession, user_id: uuid.UUID,
) -> list[str]:
    """Return the list of active platform role CODES for a user."""
    result = await db.execute(
        select(PlatformRole.code)
        .join(UserPlatformRole, UserPlatformRole.platform_role_id == PlatformRole.id)
        .where(
            UserPlatformRole.user_id == user_id,
            PlatformRole.is_active.is_(True),
        )
    )
    return [row[0] for row in result.all()]


async def _get_plan_by_code(db: AsyncSession, code: str) -> SubscriptionPlan:
    plan = await db.scalar(select(SubscriptionPlan).where(SubscriptionPlan.code == code))
    if plan is None:
        raise NotFoundError(f"Subscription plan '{code}' not found.")
    return plan


# =====================================================================
# Roles
# =====================================================================


class PlatformRoleService:

    @staticmethod
    async def list_roles(db: AsyncSession) -> list[PlatformRole]:
        result = await db.execute(
            select(PlatformRole).order_by(PlatformRole.code)
        )
        return list(result.scalars().all())

    @staticmethod
    async def get_user_roles_codes(db: AsyncSession, user_id: uuid.UUID) -> list[str]:
        return await _get_user_platform_role_codes(db, user_id)

    @staticmethod
    async def grant_role(
        db: AsyncSession,
        actor_id: uuid.UUID,
        target_user_id: uuid.UUID,
        role_code: str,
        request: Request | None = None,
    ) -> UserPlatformRole:
        target = await db.get(User, target_user_id)
        if target is None:
            raise NotFoundError("User not found.")

        role = await db.scalar(
            select(PlatformRole).where(PlatformRole.code == role_code),
        )
        if role is None:
            raise NotFoundError(f"Platform role '{role_code}' not found.")

        existing = await db.scalar(
            select(UserPlatformRole).where(
                UserPlatformRole.user_id == target_user_id,
                UserPlatformRole.platform_role_id == role.id,
            )
        )
        if existing:
            return existing

        grant = UserPlatformRole(
            user_id=target_user_id,
            platform_role_id=role.id,
            granted_by=actor_id,
        )
        db.add(grant)
        await db.flush()
        await db.refresh(grant)

        await write_audit(
            db, actor_id, "platform_role.grant",
            "user", target_user_id,
            payload={"role_code": role_code},
            request=request,
        )
        return grant

    @staticmethod
    async def revoke_role(
        db: AsyncSession,
        actor_id: uuid.UUID,
        target_user_id: uuid.UUID,
        role_code: str,
        request: Request | None = None,
    ) -> None:
        role = await db.scalar(
            select(PlatformRole).where(PlatformRole.code == role_code),
        )
        if role is None:
            raise NotFoundError(f"Platform role '{role_code}' not found.")

        grant = await db.scalar(
            select(UserPlatformRole).where(
                UserPlatformRole.user_id == target_user_id,
                UserPlatformRole.platform_role_id == role.id,
            )
        )
        if grant is None:
            raise NotFoundError("Role grant not found for this user.")

        # Safety: cannot revoke your own super_admin (foot-gun protection)
        if actor_id == target_user_id and role_code == "super_admin":
            raise ValidationError("You cannot revoke your own super_admin role.")

        await db.delete(grant)
        await db.flush()

        await write_audit(
            db, actor_id, "platform_role.revoke",
            "user", target_user_id,
            payload={"role_code": role_code},
            request=request,
        )


# =====================================================================
# Plans
# =====================================================================


class PlanService:

    @staticmethod
    async def list_plans(
        db: AsyncSession, include_inactive: bool = False,
    ) -> list[SubscriptionPlan]:
        stmt = select(SubscriptionPlan).order_by(SubscriptionPlan.sort_order, SubscriptionPlan.tier)
        if not include_inactive:
            stmt = stmt.where(SubscriptionPlan.is_active.is_(True))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_plan(db: AsyncSession, plan_id: uuid.UUID) -> SubscriptionPlan:
        plan = await db.get(SubscriptionPlan, plan_id)
        if plan is None:
            raise NotFoundError("Plan not found.")
        return plan

    @staticmethod
    async def create_plan(
        db: AsyncSession, actor_id: uuid.UUID, data: PlanCreate,
        request: Request | None = None,
    ) -> SubscriptionPlan:
        existing = await db.scalar(
            select(SubscriptionPlan).where(SubscriptionPlan.code == data.code),
        )
        if existing:
            raise ConflictError(f"A plan with code '{data.code}' already exists.")

        plan = SubscriptionPlan(**data.model_dump())
        db.add(plan)
        await db.flush()
        await db.refresh(plan)

        await write_audit(
            db, actor_id, "plan.create",
            "plan", plan.id,
            payload={"code": data.code, "name": data.name},
            request=request,
        )
        return plan

    @staticmethod
    async def update_plan(
        db: AsyncSession, actor_id: uuid.UUID,
        plan_id: uuid.UUID, data: PlanUpdate,
        request: Request | None = None,
    ) -> SubscriptionPlan:
        plan = await PlanService.get_plan(db, plan_id)
        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(plan, field, value)
        await db.flush()
        await db.refresh(plan)

        await write_audit(
            db, actor_id, "plan.update",
            "plan", plan_id,
            payload=updates,
            request=request,
        )
        return plan

    @staticmethod
    async def delete_plan(
        db: AsyncSession, actor_id: uuid.UUID, plan_id: uuid.UUID,
        request: Request | None = None,
    ) -> None:
        plan = await PlanService.get_plan(db, plan_id)

        # Cannot delete plan with active subscriptions
        in_use = await db.scalar(
            select(func.count(OrganizationSubscription.id)).where(
                OrganizationSubscription.plan_id == plan_id,
                OrganizationSubscription.status.in_(("trial", "active", "past_due")),
            )
        )
        if in_use:
            raise ConflictError(
                f"Cannot delete plan — {in_use} active subscription(s) still reference it. "
                "Move them to another plan or deactivate instead.",
            )

        # Soft delete: mark as inactive
        plan.is_active = False
        plan.is_public = False
        await db.flush()

        await write_audit(
            db, actor_id, "plan.deactivate",
            "plan", plan_id,
            payload={"code": plan.code},
            request=request,
        )


# =====================================================================
# Features
# =====================================================================


class FeatureService:

    @staticmethod
    async def list_features(db: AsyncSession) -> list[PlatformFeature]:
        result = await db.execute(
            select(PlatformFeature).order_by(PlatformFeature.category, PlatformFeature.key)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_feature(
        db: AsyncSession, actor_id: uuid.UUID, data: FeatureCreate,
        request: Request | None = None,
    ) -> PlatformFeature:
        existing = await db.scalar(
            select(PlatformFeature).where(PlatformFeature.key == data.key),
        )
        if existing:
            raise ConflictError(f"A feature with key '{data.key}' already exists.")

        feat = PlatformFeature(**data.model_dump())
        db.add(feat)
        await db.flush()
        await db.refresh(feat)

        await write_audit(
            db, actor_id, "feature.create",
            "feature", feat.id,
            payload={"key": data.key},
            request=request,
        )
        return feat

    @staticmethod
    async def list_plan_features(
        db: AsyncSession, plan_id: uuid.UUID,
    ) -> list[PlanFeature]:
        result = await db.execute(
            select(PlanFeature).where(PlanFeature.plan_id == plan_id)
        )
        return list(result.scalars().all())

    @staticmethod
    async def set_plan_feature(
        db: AsyncSession, actor_id: uuid.UUID,
        plan_id: uuid.UUID, data: PlanFeatureSet,
        request: Request | None = None,
    ) -> PlanFeature:
        existing = await db.scalar(
            select(PlanFeature).where(
                PlanFeature.plan_id == plan_id,
                PlanFeature.feature_id == data.feature_id,
            )
        )
        if existing is None:
            existing = PlanFeature(
                plan_id=plan_id,
                feature_id=data.feature_id,
                enabled=data.enabled,
                limit_value=data.limit_value,
            )
            db.add(existing)
        else:
            existing.enabled = data.enabled
            existing.limit_value = data.limit_value

        await db.flush()
        await db.refresh(existing)

        await write_audit(
            db, actor_id, "plan_feature.set",
            "plan", plan_id,
            payload={
                "feature_id": str(data.feature_id),
                "enabled": data.enabled,
                "limit_value": data.limit_value,
            },
            request=request,
        )
        return existing

    @staticmethod
    async def remove_plan_feature(
        db: AsyncSession, actor_id: uuid.UUID,
        plan_id: uuid.UUID, feature_id: uuid.UUID,
        request: Request | None = None,
    ) -> None:
        row = await db.scalar(
            select(PlanFeature).where(
                PlanFeature.plan_id == plan_id,
                PlanFeature.feature_id == feature_id,
            )
        )
        if row is None:
            return
        await db.delete(row)
        await db.flush()
        await write_audit(
            db, actor_id, "plan_feature.remove",
            "plan", plan_id,
            payload={"feature_id": str(feature_id)},
            request=request,
        )


# =====================================================================
# Subscriptions
# =====================================================================


class SubscriptionService:

    @staticmethod
    async def list_subscriptions(
        db: AsyncSession,
        status: str | None = None,
        plan_code: str | None = None,
    ) -> list[tuple[OrganizationSubscription, Organization, SubscriptionPlan]]:
        stmt = (
            select(OrganizationSubscription, Organization, SubscriptionPlan)
            .join(Organization, Organization.id == OrganizationSubscription.organization_id)
            .join(SubscriptionPlan, SubscriptionPlan.id == OrganizationSubscription.plan_id)
            .order_by(OrganizationSubscription.updated_at.desc())
        )
        if status:
            stmt = stmt.where(OrganizationSubscription.status == status)
        if plan_code:
            stmt = stmt.where(SubscriptionPlan.code == plan_code)
        result = await db.execute(stmt)
        return list(result.all())

    @staticmethod
    async def get_active_for_org(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> OrganizationSubscription | None:
        return await db.scalar(
            select(OrganizationSubscription)
            .where(
                OrganizationSubscription.organization_id == org_id,
                OrganizationSubscription.status.in_(("trial", "active", "past_due")),
            )
            .order_by(OrganizationSubscription.updated_at.desc())
        )

    @staticmethod
    async def create_subscription(
        db: AsyncSession, actor_id: uuid.UUID,
        data: SubscriptionCreate,
        request: Request | None = None,
    ) -> OrganizationSubscription:
        org = await db.get(Organization, data.organization_id)
        if org is None:
            raise NotFoundError("Organization not found.")
        plan = await _get_plan_by_code(db, data.plan_code)

        # Cancel any existing active-ish subscription
        active = await SubscriptionService.get_active_for_org(db, data.organization_id)
        if active is not None:
            active.status = "cancelled"
            active.cancelled_at = datetime.now(UTC)
            active.cancelled_by = actor_id
            await db.flush()

        sub = OrganizationSubscription(
            organization_id=data.organization_id,
            plan_id=plan.id,
            status=data.status,
            billing_cycle=data.billing_cycle,
            started_at=data.started_at or date.today(),
            expires_at=data.expires_at,
            trial_ends_at=data.trial_ends_at,
            auto_renew=data.auto_renew,
            notes=data.notes,
            created_by=actor_id,
        )
        db.add(sub)
        await db.flush()
        await db.refresh(sub)

        await write_audit(
            db, actor_id, "subscription.create",
            "subscription", sub.id,
            target_org_id=data.organization_id,
            payload={"plan_code": data.plan_code, "status": data.status},
            request=request,
        )
        return sub

    @staticmethod
    async def update_subscription(
        db: AsyncSession, actor_id: uuid.UUID,
        subscription_id: uuid.UUID, data: SubscriptionUpdate,
        request: Request | None = None,
    ) -> OrganizationSubscription:
        sub = await db.get(OrganizationSubscription, subscription_id)
        if sub is None:
            raise NotFoundError("Subscription not found.")

        updates = data.model_dump(exclude_unset=True)

        # Plan switch
        if "plan_code" in updates:
            new_code = updates.pop("plan_code")
            new_plan = await _get_plan_by_code(db, new_code)
            sub.plan_id = new_plan.id

        # Cancellation tracking
        if updates.get("status") == "cancelled" and sub.status != "cancelled":
            sub.cancelled_at = datetime.now(UTC)
            sub.cancelled_by = actor_id

        for field, value in updates.items():
            setattr(sub, field, value)
        await db.flush()
        await db.refresh(sub)

        await write_audit(
            db, actor_id, "subscription.update",
            "subscription", subscription_id,
            target_org_id=sub.organization_id,
            payload=data.model_dump(exclude_unset=True),
            request=request,
        )
        return sub

    @staticmethod
    async def activate_subscription(
        db: AsyncSession, actor_id: uuid.UUID, subscription_id: uuid.UUID,
        request: Request | None = None,
    ) -> OrganizationSubscription:
        return await SubscriptionService.update_subscription(
            db, actor_id, subscription_id,
            SubscriptionUpdate(status="active"), request,
        )

    @staticmethod
    async def suspend_subscription(
        db: AsyncSession, actor_id: uuid.UUID, subscription_id: uuid.UUID,
        request: Request | None = None,
    ) -> OrganizationSubscription:
        return await SubscriptionService.update_subscription(
            db, actor_id, subscription_id,
            SubscriptionUpdate(status="suspended", auto_renew=False), request,
        )


# =====================================================================
# Organizations (admin view)
# =====================================================================


class PlatformOrgService:

    @staticmethod
    async def list_organizations(
        db: AsyncSession,
        search: str | None = None,
        type_: str | None = None,
        status: str | None = None,
    ) -> list[dict]:
        """Return orgs with member count + subscription summary."""
        stmt = (
            select(
                Organization,
                SubscriptionPlan,
                OrganizationSubscription,
                func.count(func.distinct(Membership.id)).label("member_count"),
            )
            .outerjoin(Membership, Membership.organization_id == Organization.id)
            .outerjoin(
                OrganizationSubscription,
                and_(
                    OrganizationSubscription.organization_id == Organization.id,
                    OrganizationSubscription.status.in_(("trial", "active", "past_due")),
                ),
            )
            .outerjoin(
                SubscriptionPlan,
                SubscriptionPlan.id == OrganizationSubscription.plan_id,
            )
            .where(Organization.deleted_at.is_(None))
            .group_by(Organization.id, SubscriptionPlan.id, OrganizationSubscription.id)
            .order_by(Organization.created_at.desc())
        )
        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                (Organization.name.ilike(term)) | (Organization.slug.ilike(term))
            )
        if type_:
            stmt = stmt.where(Organization.type == type_)
        if status:
            stmt = stmt.where(OrganizationSubscription.status == status)

        result = await db.execute(stmt)
        rows = result.all()

        return [
            {
                "id": org.id,
                "name": org.name,
                "slug": org.slug,
                "type": org.type,
                "created_at": org.created_at,
                "member_count": int(member_count or 0),
                "subscription_status": sub.status if sub else None,
                "plan_name": plan.name if plan else None,
                "plan_code": plan.code if plan else None,
            }
            for org, plan, sub, member_count in rows
        ]

    @staticmethod
    async def get_organization(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> dict:
        org = await db.get(Organization, org_id)
        if org is None or org.deleted_at is not None:
            raise NotFoundError("Organization not found.")

        member_count = await db.scalar(
            select(func.count(Membership.id)).where(Membership.organization_id == org_id)
        )
        sub = await SubscriptionService.get_active_for_org(db, org_id)
        plan = await db.get(SubscriptionPlan, sub.plan_id) if sub else None

        return {
            "id": org.id,
            "name": org.name,
            "slug": org.slug,
            "type": org.type,
            "settings": org.settings or {},
            "created_at": org.created_at,
            "updated_at": org.updated_at,
            "member_count": int(member_count or 0),
            "subscription": sub,
            "plan_name": plan.name if plan else None,
        }

    @staticmethod
    async def create_organization(
        db: AsyncSession, actor_id: uuid.UUID, data: PlatformOrgCreate,
        request: Request | None = None,
    ) -> Organization:
        # Unique slug + email checks
        if await db.scalar(select(Organization).where(Organization.slug == data.slug)):
            raise ConflictError("An organization with this slug already exists.")
        if await db.scalar(select(User).where(User.email == data.owner_email)):
            raise ConflictError("A user with this email already exists.")

        plan = await _get_plan_by_code(db, data.plan_code)

        # Create org
        org = Organization(name=data.name, slug=data.slug, type=data.type)
        db.add(org)
        await db.flush()

        # Create owner user
        owner = User(
            name=data.owner_name,
            email=data.owner_email,
            password_hash=hash_password(data.owner_password),
        )
        db.add(owner)
        await db.flush()

        # Membership as owner
        db.add(Membership(
            organization_id=org.id,
            user_id=owner.id,
            role="owner",
        ))

        # Trial subscription
        trial_ends = date.today() + timedelta(days=data.trial_days) if data.trial_days > 0 else None
        db.add(OrganizationSubscription(
            organization_id=org.id,
            plan_id=plan.id,
            status="trial" if data.trial_days > 0 else "active",
            billing_cycle="monthly",
            started_at=date.today(),
            trial_ends_at=trial_ends,
            created_by=actor_id,
            notes=f"Created by platform admin for {data.owner_email}",
        ))

        await db.flush()
        await db.refresh(org)

        await write_audit(
            db, actor_id, "organization.create",
            "organization", org.id,
            target_org_id=org.id,
            payload={
                "name": data.name,
                "slug": data.slug,
                "owner_email": data.owner_email,
                "plan_code": data.plan_code,
            },
            request=request,
        )
        return org

    @staticmethod
    async def update_organization(
        db: AsyncSession, actor_id: uuid.UUID,
        org_id: uuid.UUID, data: PlatformOrgUpdate,
        request: Request | None = None,
    ) -> Organization:
        org = await db.get(Organization, org_id)
        if org is None or org.deleted_at is not None:
            raise NotFoundError("Organization not found.")
        if org.type == "platform":
            raise ValidationError("Cannot modify the platform owner organization.")

        updates = data.model_dump(exclude_unset=True)
        for field, value in updates.items():
            setattr(org, field, value)
        await db.flush()
        await db.refresh(org)

        await write_audit(
            db, actor_id, "organization.update",
            "organization", org_id,
            target_org_id=org_id,
            payload=updates,
            request=request,
        )
        return org

    @staticmethod
    async def soft_delete_organization(
        db: AsyncSession, actor_id: uuid.UUID, org_id: uuid.UUID,
        request: Request | None = None,
    ) -> None:
        org = await db.get(Organization, org_id)
        if org is None:
            raise NotFoundError("Organization not found.")
        if org.type == "platform":
            raise ValidationError("Cannot delete the platform owner organization.")

        org.deleted_at = datetime.now(UTC)
        await db.flush()

        await write_audit(
            db, actor_id, "organization.delete",
            "organization", org_id,
            target_org_id=org_id,
            request=request,
        )


# =====================================================================
# Platform users (admin view)
# =====================================================================


class PlatformUserService:

    @staticmethod
    async def list_users(
        db: AsyncSession,
        search: str | None = None,
        with_platform_role: bool | None = None,
    ) -> list[dict]:
        stmt = (
            select(
                User,
                func.count(func.distinct(Membership.id)).label("org_count"),
            )
            .outerjoin(Membership, Membership.user_id == User.id)
            .where(User.deleted_at.is_(None))
            .group_by(User.id)
            .order_by(User.created_at.desc())
        )
        if search:
            term = f"%{search}%"
            stmt = stmt.where((User.name.ilike(term)) | (User.email.ilike(term)))

        result = await db.execute(stmt)
        rows = result.all()

        # Fetch platform roles in one query
        role_rows = await db.execute(
            select(UserPlatformRole.user_id, PlatformRole.code)
            .join(PlatformRole, PlatformRole.id == UserPlatformRole.platform_role_id)
        )
        roles_by_user: dict[uuid.UUID, list[str]] = {}
        for uid, code in role_rows.all():
            roles_by_user.setdefault(uid, []).append(code)

        items = [
            {
                "id": u.id,
                "name": u.name,
                "email": u.email,
                "created_at": u.created_at,
                "last_login_at": u.last_login_at,
                "deleted_at": u.deleted_at,
                "organization_count": int(oc or 0),
                "platform_roles": roles_by_user.get(u.id, []),
            }
            for u, oc in rows
        ]

        if with_platform_role is True:
            items = [i for i in items if i["platform_roles"]]
        elif with_platform_role is False:
            items = [i for i in items if not i["platform_roles"]]

        return items


# =====================================================================
# Feature overrides
# =====================================================================


class OverrideService:

    @staticmethod
    async def list_for_org(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[OrganizationFeatureOverride]:
        result = await db.execute(
            select(OrganizationFeatureOverride)
            .where(OrganizationFeatureOverride.organization_id == org_id)
            .order_by(OrganizationFeatureOverride.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def set_override(
        db: AsyncSession, actor_id: uuid.UUID,
        org_id: uuid.UUID, data: OverrideSet,
        request: Request | None = None,
    ) -> OrganizationFeatureOverride:
        feature = await db.scalar(
            select(PlatformFeature).where(PlatformFeature.key == data.feature_key),
        )
        if feature is None:
            raise NotFoundError(f"Feature '{data.feature_key}' not found.")

        existing = await db.scalar(
            select(OrganizationFeatureOverride).where(
                OrganizationFeatureOverride.organization_id == org_id,
                OrganizationFeatureOverride.feature_id == feature.id,
            )
        )
        if existing is None:
            existing = OrganizationFeatureOverride(
                organization_id=org_id,
                feature_id=feature.id,
                enabled=data.enabled,
                limit_value=data.limit_value,
                reason=data.reason,
                granted_by=actor_id,
                expires_at=data.expires_at,
            )
            db.add(existing)
        else:
            existing.enabled = data.enabled
            existing.limit_value = data.limit_value
            existing.reason = data.reason
            existing.granted_by = actor_id
            existing.expires_at = data.expires_at

        await db.flush()
        await db.refresh(existing)

        await write_audit(
            db, actor_id, "override.set",
            "organization", org_id,
            target_org_id=org_id,
            payload={
                "feature_key": data.feature_key,
                "enabled": data.enabled,
                "limit_value": data.limit_value,
                "reason": data.reason,
            },
            request=request,
        )
        return existing

    @staticmethod
    async def remove_override(
        db: AsyncSession, actor_id: uuid.UUID,
        org_id: uuid.UUID, feature_key: str,
        request: Request | None = None,
    ) -> None:
        feature = await db.scalar(
            select(PlatformFeature).where(PlatformFeature.key == feature_key),
        )
        if feature is None:
            raise NotFoundError(f"Feature '{feature_key}' not found.")

        row = await db.scalar(
            select(OrganizationFeatureOverride).where(
                OrganizationFeatureOverride.organization_id == org_id,
                OrganizationFeatureOverride.feature_id == feature.id,
            )
        )
        if row:
            await db.delete(row)
            await db.flush()
            await write_audit(
                db, actor_id, "override.remove",
                "organization", org_id,
                target_org_id=org_id,
                payload={"feature_key": feature_key},
                request=request,
            )


# =====================================================================
# Audit log
# =====================================================================


class AuditService:

    @staticmethod
    async def list_entries(
        db: AsyncSession,
        actor_id: uuid.UUID | None = None,
        action: str | None = None,
        target_org_id: uuid.UUID | None = None,
        limit: int = 100,
    ) -> list[PlatformAuditLog]:
        stmt = (
            select(PlatformAuditLog)
            .order_by(PlatformAuditLog.created_at.desc())
            .limit(limit)
        )
        if actor_id:
            stmt = stmt.where(PlatformAuditLog.actor_user_id == actor_id)
        if action:
            stmt = stmt.where(PlatformAuditLog.action == action)
        if target_org_id:
            stmt = stmt.where(PlatformAuditLog.target_org_id == target_org_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())


# =====================================================================
# Dashboard
# =====================================================================


class PlatformAppService:
    """Super-admin operations on app registry, org apps, and app roles."""

    # ------------------------------------------------------------------
    # Registry + catalog (read)
    # ------------------------------------------------------------------

    @staticmethod
    async def list_apps(db: AsyncSession) -> list[AppRegistry]:
        result = await db.execute(
            select(AppRegistry)
            .where(AppRegistry.is_active.is_(True))
            .order_by(AppRegistry.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_role_catalog(
        db: AsyncSession, app_code: str,
    ) -> list[AppRoleCatalog]:
        result = await db.execute(
            select(AppRoleCatalog)
            .where(
                AppRoleCatalog.app_code == app_code,
                AppRoleCatalog.is_active.is_(True),
            )
            .order_by(AppRoleCatalog.sort_order, AppRoleCatalog.code)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Per-org app activation
    # ------------------------------------------------------------------

    @staticmethod
    async def list_org_apps(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[dict]:
        """Return every app in the registry + whether this org has it activated."""
        apps = await db.execute(
            select(AppRegistry)
            .where(AppRegistry.is_active.is_(True))
            .order_by(AppRegistry.name)
        )
        app_rows = list(apps.scalars().all())

        activations = await db.execute(
            select(OrganizationApp).where(
                OrganizationApp.organization_id == org_id,
            )
        )
        by_app_id: dict[uuid.UUID, OrganizationApp] = {
            oa.app_id: oa for oa in activations.scalars().all()
        }

        result = []
        for app in app_rows:
            oa = by_app_id.get(app.id)
            is_active = oa is not None and oa.status in ("active", "trial")
            result.append({
                "app_code": app.code,
                "app_name": app.name,
                "app_icon": app.icon,
                "app_color": app.color,
                "is_active": is_active,
                "status": oa.status if oa else None,
                "activated_at": oa.activated_at if oa else None,
                "trial_ends_at": oa.trial_ends_at if oa else None,
                "expires_at": oa.expires_at if oa else None,
            })
        return result

    @staticmethod
    async def activate_org_app(
        db: AsyncSession, actor_id: uuid.UUID,
        org_id: uuid.UUID, app_code: str,
        request: Request | None = None,
    ) -> OrganizationApp:
        org = await db.get(Organization, org_id)
        if org is None or org.deleted_at is not None:
            raise NotFoundError("Organization not found.")
        if org.type == "platform":
            raise ValidationError("Cannot activate apps for the platform owner org.")

        app = await db.scalar(
            select(AppRegistry).where(
                AppRegistry.code == app_code,
                AppRegistry.is_active.is_(True),
            )
        )
        if app is None:
            raise NotFoundError(f"App '{app_code}' not found.")

        # Existing active row? Re-activate if cancelled; no-op if already on.
        existing = await db.scalar(
            select(OrganizationApp).where(
                OrganizationApp.organization_id == org_id,
                OrganizationApp.app_id == app.id,
            )
        )
        now = datetime.now(UTC)
        if existing is not None:
            if existing.status in ("active", "trial"):
                return existing
            existing.status = "active"
            existing.activated_at = now
            existing.trial_ends_at = None
            existing.expires_at = None
            org_app = existing
        else:
            org_app = OrganizationApp(
                organization_id=org_id,
                app_id=app.id,
                status="active",
                activated_at=now,
            )
            db.add(org_app)
        await db.flush()
        await db.refresh(org_app)

        await write_audit(
            db, actor_id, "org_app.activate",
            "organization", org_id,
            target_org_id=org_id,
            payload={"app_code": app_code},
            request=request,
        )
        return org_app

    @staticmethod
    async def deactivate_org_app(
        db: AsyncSession, actor_id: uuid.UUID,
        org_id: uuid.UUID, app_code: str,
        request: Request | None = None,
    ) -> None:
        app = await db.scalar(
            select(AppRegistry).where(AppRegistry.code == app_code)
        )
        if app is None:
            raise NotFoundError(f"App '{app_code}' not found.")

        org_app = await db.scalar(
            select(OrganizationApp).where(
                OrganizationApp.organization_id == org_id,
                OrganizationApp.app_id == app.id,
                OrganizationApp.status.in_(("active", "trial")),
            )
        )
        if org_app is None:
            return
        org_app.status = "cancelled"
        await db.flush()

        await write_audit(
            db, actor_id, "org_app.deactivate",
            "organization", org_id,
            target_org_id=org_id,
            payload={"app_code": app_code},
            request=request,
        )

    # ------------------------------------------------------------------
    # Org members + per-app roles
    # ------------------------------------------------------------------

    @staticmethod
    async def list_org_members(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[dict]:
        """Members of an org + their roles across apps."""
        member_rows = await db.execute(
            select(Membership, User)
            .join(User, User.id == Membership.user_id)
            .where(Membership.organization_id == org_id)
            .order_by(Membership.joined_at)
        )
        members = member_rows.all()

        role_rows = await db.execute(
            select(AppUserRole, AppRegistry.code, AppRegistry.name)
            .join(AppRegistry, AppRegistry.id == AppUserRole.app_id)
            .where(AppUserRole.organization_id == org_id)
        )
        roles_by_user: dict[uuid.UUID, list[dict]] = {}
        for aur, app_code, app_name in role_rows.all():
            roles_by_user.setdefault(aur.user_id, []).append({
                "app_code": app_code,
                "app_name": app_name,
                "role": aur.role,
            })

        return [
            {
                "user_id": u.id,
                "name": u.name,
                "email": u.email,
                "membership_id": m.id,
                "membership_role": m.role,
                "joined_at": m.joined_at,
                "app_roles": roles_by_user.get(u.id, []),
            }
            for m, u in members
        ]

    @staticmethod
    async def invite_member(
        db: AsyncSession, actor_id: uuid.UUID,
        org_id: uuid.UUID, data: InviteMemberRequest,
        request: Request | None = None,
    ) -> Membership:
        org = await db.get(Organization, org_id)
        if org is None or org.deleted_at is not None:
            raise NotFoundError("Organization not found.")
        if org.type == "platform":
            raise ValidationError("Cannot invite members to the platform owner org.")

        existing = await db.scalar(select(User).where(User.email == data.email))
        if existing is None:
            user = User(
                name=data.name,
                email=data.email,
                password_hash=hash_password(data.password),
            )
            db.add(user)
            await db.flush()
        else:
            user = existing
            # Already a member?
            dup = await db.scalar(
                select(Membership).where(
                    Membership.organization_id == org_id,
                    Membership.user_id == user.id,
                )
            )
            if dup is not None:
                raise ConflictError("User is already a member of this organization.")

        membership = Membership(
            organization_id=org_id,
            user_id=user.id,
            role=data.membership_role,
        )
        db.add(membership)
        await db.flush()
        await db.refresh(membership)

        await write_audit(
            db, actor_id, "member.invite",
            "user", user.id,
            target_org_id=org_id,
            payload={"email": data.email, "role": data.membership_role},
            request=request,
        )
        return membership

    @staticmethod
    async def remove_member(
        db: AsyncSession, actor_id: uuid.UUID,
        org_id: uuid.UUID, user_id: uuid.UUID,
        request: Request | None = None,
    ) -> None:
        membership = await db.scalar(
            select(Membership).where(
                Membership.organization_id == org_id,
                Membership.user_id == user_id,
            )
        )
        if membership is None:
            raise NotFoundError("Membership not found.")
        if membership.role == "owner":
            raise ValidationError("Cannot remove the owner directly. Transfer ownership first.")

        # Also delete app-level roles for this user in the org
        roles = await db.execute(
            select(AppUserRole).where(
                AppUserRole.organization_id == org_id,
                AppUserRole.user_id == user_id,
            )
        )
        for r in roles.scalars().all():
            await db.delete(r)
        await db.delete(membership)
        await db.flush()

        await write_audit(
            db, actor_id, "member.remove",
            "user", user_id,
            target_org_id=org_id,
            request=request,
        )

    @staticmethod
    async def assign_app_role(
        db: AsyncSession, actor_id: uuid.UUID,
        org_id: uuid.UUID, data: AssignAppRoleRequest,
        request: Request | None = None,
    ) -> AppUserRole:
        # Validate target user is a member
        membership = await db.scalar(
            select(Membership).where(
                Membership.organization_id == org_id,
                Membership.user_id == data.user_id,
            )
        )
        if membership is None:
            raise NotFoundError("User is not a member of this organization.")

        # Validate app + role catalog
        app = await db.scalar(
            select(AppRegistry).where(AppRegistry.code == data.app_code)
        )
        if app is None:
            raise NotFoundError(f"App '{data.app_code}' not found.")

        role_def = await db.scalar(
            select(AppRoleCatalog).where(
                AppRoleCatalog.app_code == data.app_code,
                AppRoleCatalog.code == data.role,
                AppRoleCatalog.is_active.is_(True),
            )
        )
        if role_def is None:
            raise ValidationError(
                f"Role '{data.role}' is not a valid role for app '{data.app_code}'.",
            )

        # Upsert
        existing = await db.scalar(
            select(AppUserRole).where(
                AppUserRole.organization_id == org_id,
                AppUserRole.user_id == data.user_id,
                AppUserRole.app_id == app.id,
            )
        )
        if existing is not None:
            existing.role = data.role
            assignment = existing
        else:
            assignment = AppUserRole(
                organization_id=org_id,
                user_id=data.user_id,
                app_id=app.id,
                role=data.role,
            )
            db.add(assignment)

        await db.flush()
        await db.refresh(assignment)

        await write_audit(
            db, actor_id, "app_role.assign",
            "user", data.user_id,
            target_org_id=org_id,
            payload={"app_code": data.app_code, "role": data.role},
            request=request,
        )
        return assignment

    @staticmethod
    async def revoke_app_role(
        db: AsyncSession, actor_id: uuid.UUID,
        org_id: uuid.UUID, user_id: uuid.UUID, app_code: str,
        request: Request | None = None,
    ) -> None:
        app = await db.scalar(
            select(AppRegistry).where(AppRegistry.code == app_code)
        )
        if app is None:
            raise NotFoundError(f"App '{app_code}' not found.")

        row = await db.scalar(
            select(AppUserRole).where(
                AppUserRole.organization_id == org_id,
                AppUserRole.user_id == user_id,
                AppUserRole.app_id == app.id,
            )
        )
        if row is None:
            return
        await db.delete(row)
        await db.flush()

        await write_audit(
            db, actor_id, "app_role.revoke",
            "user", user_id,
            target_org_id=org_id,
            payload={"app_code": app_code},
            request=request,
        )


class DashboardService:

    @staticmethod
    async def get_kpis(db: AsyncSession) -> dict:
        # Totals
        total_orgs = await db.scalar(
            select(func.count(Organization.id)).where(Organization.deleted_at.is_(None))
        )
        active_orgs = await db.scalar(
            select(func.count(func.distinct(OrganizationSubscription.organization_id)))
            .where(OrganizationSubscription.status == "active")
        )
        trial_orgs = await db.scalar(
            select(func.count(func.distinct(OrganizationSubscription.organization_id)))
            .where(OrganizationSubscription.status == "trial")
        )
        suspended_orgs = await db.scalar(
            select(func.count(func.distinct(OrganizationSubscription.organization_id)))
            .where(OrganizationSubscription.status == "suspended")
        )
        total_users = await db.scalar(
            select(func.count(User.id)).where(User.deleted_at.is_(None))
        )

        # MRR estimation: sum of price_monthly for all active (non-trial, non-platform) subscriptions
        mrr_rows = await db.execute(
            select(
                SubscriptionPlan.price_monthly,
                SubscriptionPlan.price_yearly,
                OrganizationSubscription.billing_cycle,
            )
            .join(
                OrganizationSubscription,
                OrganizationSubscription.plan_id == SubscriptionPlan.id,
            )
            .where(
                OrganizationSubscription.status == "active",
                SubscriptionPlan.code != "platform",
            )
        )
        mrr = Decimal("0")
        for price_m, price_y, cycle in mrr_rows.all():
            if cycle == "yearly":
                mrr += (price_y or Decimal("0")) / Decimal("12")
            else:
                mrr += price_m or Decimal("0")

        # New orgs last 30 days
        thirty_days_ago = datetime.now(UTC) - timedelta(days=30)
        new_orgs = await db.scalar(
            select(func.count(Organization.id)).where(
                Organization.deleted_at.is_(None),
                Organization.created_at >= thirty_days_ago,
            )
        )
        cancelled = await db.scalar(
            select(func.count(OrganizationSubscription.id)).where(
                OrganizationSubscription.status == "cancelled",
                OrganizationSubscription.cancelled_at >= thirty_days_ago,
            )
        )

        # Breakdown by plan
        plan_rows = await db.execute(
            select(SubscriptionPlan.code, func.count(OrganizationSubscription.id))
            .join(
                OrganizationSubscription,
                OrganizationSubscription.plan_id == SubscriptionPlan.id,
            )
            .where(OrganizationSubscription.status.in_(("trial", "active", "past_due")))
            .group_by(SubscriptionPlan.code)
        )
        by_plan = {row[0]: row[1] for row in plan_rows.all()}

        return {
            "total_organizations": int(total_orgs or 0),
            "active_organizations": int(active_orgs or 0),
            "trial_organizations": int(trial_orgs or 0),
            "suspended_organizations": int(suspended_orgs or 0),
            "total_users": int(total_users or 0),
            "mrr": mrr.quantize(Decimal("0.01")),
            "new_orgs_last_30d": int(new_orgs or 0),
            "cancelled_last_30d": int(cancelled or 0),
            "subscriptions_by_plan": by_plan,
        }
