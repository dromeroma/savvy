"""Savvy Platform admin REST endpoints.

All endpoints live under /api/v1/platform and are guarded by
`require_super_admin`. Super admins operate exclusively from this
surface — they never enter organizations themselves.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db
from src.modules.platform.dependencies import require_super_admin
from src.modules.platform.schemas import (
    AppPermissionResponse,
    AppRegistryResponse,
    AppRoleCatalogResponse,
    AssignAppRoleRequest,
    AuditLogEntry,
    CustomRoleCreate,
    CustomRoleUpdate,
    DashboardKPIs,
    FeatureCreate,
    FeatureResponse,
    FeatureUpdate,
    GrantRoleRequest,
    InviteMemberRequest,
    OrgAppActivateRequest,
    OrgAppSummary,
    OrgMemberSummary,
    OverrideResponse,
    OverrideSet,
    PlanCreate,
    PlanFeatureResponse,
    PlanFeatureSet,
    PlanResponse,
    PlanUpdate,
    PlatformOrgCreate,
    PlatformOrgDetail,
    PlatformOrgSummary,
    PlatformOrgUpdate,
    PlatformRoleResponse,
    PlatformUserSummary,
    ResetPasswordRequest,
    SubscriptionCreate,
    SubscriptionResponse,
    SubscriptionUpdate,
    TimeseriesPoint,
    UserPlatformRoleResponse,
)
from src.modules.platform.service import (
    AuditService,
    DashboardService,
    FeatureService,
    OverrideService,
    PlanService,
    PlatformAppService,
    PlatformOrgService,
    PlatformRoleService,
    PlatformUserService,
    SubscriptionService,
)

router = APIRouter(
    prefix="/platform",
    tags=["Savvy Platform"],
    dependencies=[Depends(require_super_admin)],
)


# =====================================================================
# Dashboard
# =====================================================================


@router.get("/dashboard", response_model=DashboardKPIs)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
) -> Any:
    """KPIs globales del ecosistema Savvy."""
    return await DashboardService.get_kpis(db)


@router.get("/dashboard/timeseries", response_model=list[TimeseriesPoint])
async def get_dashboard_timeseries(
    months: int = Query(12, ge=1, le=36),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Monthly new orgs + new users for the last N months (default 12)."""
    return await DashboardService.get_timeseries(db, months)


# =====================================================================
# Organizations
# =====================================================================


@router.get("/organizations", response_model=list[PlatformOrgSummary])
async def list_organizations(
    search: str | None = Query(None),
    type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlatformOrgService.list_organizations(
        db, search, type, status_filter,
    )


@router.get("/organizations/{org_id}", response_model=PlatformOrgDetail)
async def get_organization(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlatformOrgService.get_organization(db, org_id)


@router.post(
    "/organizations",
    response_model=PlatformOrgDetail,
    status_code=status.HTTP_201_CREATED,
)
async def create_organization(
    data: PlatformOrgCreate,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    org = await PlatformOrgService.create_organization(
        db, uuid.UUID(user["sub"]), data, request,
    )
    return await PlatformOrgService.get_organization(db, org.id)


@router.patch("/organizations/{org_id}", response_model=PlatformOrgDetail)
async def update_organization(
    org_id: uuid.UUID,
    data: PlatformOrgUpdate,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await PlatformOrgService.update_organization(
        db, uuid.UUID(user["sub"]), org_id, data, request,
    )
    return await PlatformOrgService.get_organization(db, org_id)


@router.delete(
    "/organizations/{org_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_organization(
    org_id: uuid.UUID,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await PlatformOrgService.soft_delete_organization(
        db, uuid.UUID(user["sub"]), org_id, request,
    )


# =====================================================================
# Plans
# =====================================================================


@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(
    include_inactive: bool = Query(False),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlanService.list_plans(db, include_inactive)


@router.get("/plans/{plan_id}", response_model=PlanResponse)
async def get_plan(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlanService.get_plan(db, plan_id)


@router.post(
    "/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED,
)
async def create_plan(
    data: PlanCreate,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlanService.create_plan(
        db, uuid.UUID(user["sub"]), data, request,
    )


@router.patch("/plans/{plan_id}", response_model=PlanResponse)
async def update_plan(
    plan_id: uuid.UUID,
    data: PlanUpdate,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlanService.update_plan(
        db, uuid.UUID(user["sub"]), plan_id, data, request,
    )


@router.delete(
    "/plans/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def deactivate_plan(
    plan_id: uuid.UUID,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await PlanService.delete_plan(
        db, uuid.UUID(user["sub"]), plan_id, request,
    )


@router.get("/plans/{plan_id}/features", response_model=list[PlanFeatureResponse])
async def list_plan_features(
    plan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await FeatureService.list_plan_features(db, plan_id)


@router.put("/plans/{plan_id}/features", response_model=PlanFeatureResponse)
async def set_plan_feature(
    plan_id: uuid.UUID,
    data: PlanFeatureSet,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await FeatureService.set_plan_feature(
        db, uuid.UUID(user["sub"]), plan_id, data, request,
    )


@router.delete(
    "/plans/{plan_id}/features/{feature_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def remove_plan_feature(
    plan_id: uuid.UUID,
    feature_id: uuid.UUID,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await FeatureService.remove_plan_feature(
        db, uuid.UUID(user["sub"]), plan_id, feature_id, request,
    )


# =====================================================================
# Features catalog
# =====================================================================


@router.get("/features", response_model=list[FeatureResponse])
async def list_features(db: AsyncSession = Depends(get_db)) -> Any:
    return await FeatureService.list_features(db)


@router.post(
    "/features", response_model=FeatureResponse, status_code=status.HTTP_201_CREATED,
)
async def create_feature(
    data: FeatureCreate,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await FeatureService.create_feature(
        db, uuid.UUID(user["sub"]), data, request,
    )


@router.patch("/features/{feature_id}", response_model=FeatureResponse)
async def update_feature(
    feature_id: uuid.UUID,
    data: FeatureUpdate,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await FeatureService.update_feature(
        db, uuid.UUID(user["sub"]), feature_id, data, request,
    )


@router.delete(
    "/features/{feature_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_feature(
    feature_id: uuid.UUID,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await FeatureService.delete_feature(
        db, uuid.UUID(user["sub"]), feature_id, request,
    )


# =====================================================================
# Subscriptions
# =====================================================================


@router.get("/subscriptions", response_model=list[dict])
async def list_subscriptions(
    status_filter: str | None = Query(None, alias="status"),
    plan_code: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    rows = await SubscriptionService.list_subscriptions(db, status_filter, plan_code)
    return [
        {
            "id": str(sub.id),
            "organization_id": str(sub.organization_id),
            "organization_name": org.name,
            "organization_slug": org.slug,
            "plan_id": str(sub.plan_id),
            "plan_code": plan.code,
            "plan_name": plan.name,
            "status": sub.status,
            "billing_cycle": sub.billing_cycle,
            "started_at": sub.started_at.isoformat() if sub.started_at else None,
            "expires_at": sub.expires_at.isoformat() if sub.expires_at else None,
            "trial_ends_at": sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
            "auto_renew": sub.auto_renew,
            "price_monthly": float(plan.price_monthly),
            "price_yearly": float(plan.price_yearly),
            "updated_at": sub.updated_at.isoformat(),
        }
        for sub, org, plan in rows
    ]


@router.post(
    "/subscriptions",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_subscription(
    data: SubscriptionCreate,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await SubscriptionService.create_subscription(
        db, uuid.UUID(user["sub"]), data, request,
    )


@router.patch("/subscriptions/{subscription_id}", response_model=SubscriptionResponse)
async def update_subscription(
    subscription_id: uuid.UUID,
    data: SubscriptionUpdate,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await SubscriptionService.update_subscription(
        db, uuid.UUID(user["sub"]), subscription_id, data, request,
    )


@router.post(
    "/subscriptions/{subscription_id}/activate",
    response_model=SubscriptionResponse,
)
async def activate_subscription(
    subscription_id: uuid.UUID,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await SubscriptionService.activate_subscription(
        db, uuid.UUID(user["sub"]), subscription_id, request,
    )


@router.post(
    "/subscriptions/{subscription_id}/suspend",
    response_model=SubscriptionResponse,
)
async def suspend_subscription(
    subscription_id: uuid.UUID,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await SubscriptionService.suspend_subscription(
        db, uuid.UUID(user["sub"]), subscription_id, request,
    )


# =====================================================================
# Platform users
# =====================================================================


@router.get("/users", response_model=list[PlatformUserSummary])
async def list_users(
    search: str | None = Query(None),
    with_platform_role: bool | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlatformUserService.list_users(db, search, with_platform_role)


@router.post(
    "/users/{user_id}/reset-password",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def reset_user_password(
    user_id: uuid.UUID,
    data: ResetPasswordRequest,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Super-admin reset of a user's password."""
    await PlatformUserService.reset_password(
        db, uuid.UUID(user["sub"]), user_id, data.new_password, request,
    )


# =====================================================================
# Platform roles catalog + grants
# =====================================================================


@router.get("/roles", response_model=list[PlatformRoleResponse])
async def list_platform_roles(db: AsyncSession = Depends(get_db)) -> Any:
    return await PlatformRoleService.list_roles(db)


@router.post(
    "/roles/grant",
    response_model=UserPlatformRoleResponse,
    status_code=status.HTTP_201_CREATED,
)
async def grant_platform_role(
    data: GrantRoleRequest,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlatformRoleService.grant_role(
        db, uuid.UUID(user["sub"]), data.user_id, data.role_code, request,
    )


@router.delete(
    "/roles/revoke",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def revoke_platform_role(
    request: Request,
    user_id: uuid.UUID = Query(...),
    role_code: str = Query(...),
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await PlatformRoleService.revoke_role(
        db, uuid.UUID(user["sub"]), user_id, role_code, request,
    )


# =====================================================================
# Feature overrides
# =====================================================================


@router.get(
    "/organizations/{org_id}/overrides",
    response_model=list[OverrideResponse],
)
async def list_overrides(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await OverrideService.list_for_org(db, org_id)


@router.put(
    "/organizations/{org_id}/overrides",
    response_model=OverrideResponse,
)
async def set_override(
    org_id: uuid.UUID,
    data: OverrideSet,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await OverrideService.set_override(
        db, uuid.UUID(user["sub"]), org_id, data, request,
    )


@router.delete(
    "/organizations/{org_id}/overrides/{feature_key}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def remove_override(
    org_id: uuid.UUID,
    feature_key: str,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await OverrideService.remove_override(
        db, uuid.UUID(user["sub"]), org_id, feature_key, request,
    )


# =====================================================================
# App registry + role catalog
# =====================================================================


@router.get("/apps", response_model=list[AppRegistryResponse])
async def list_platform_apps(db: AsyncSession = Depends(get_db)) -> Any:
    """List every app in the Savvy ecosystem registry."""
    return await PlatformAppService.list_apps(db)


@router.get(
    "/apps/{app_code}/roles",
    response_model=list[AppRoleCatalogResponse],
)
async def list_app_role_catalog(
    app_code: str,
    organization_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List valid roles for the given app.

    If `organization_id` is provided, includes custom roles owned by that org
    in addition to the system roles.
    """
    return await PlatformAppService.list_role_catalog(db, app_code, organization_id)


@router.get(
    "/apps/{app_code}/permissions",
    response_model=list[AppPermissionResponse],
)
async def list_app_permissions(
    app_code: str,
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List the permission catalog for the given app."""
    return await PlatformAppService.list_permissions_catalog(db, app_code)


@router.get(
    "/organizations/{org_id}/custom-roles",
    response_model=list[AppRoleCatalogResponse],
)
async def list_org_custom_roles(
    org_id: uuid.UUID,
    app_code: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlatformAppService.list_org_custom_roles(db, org_id, app_code)


@router.post(
    "/organizations/{org_id}/custom-roles",
    response_model=AppRoleCatalogResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_org_custom_role(
    org_id: uuid.UUID,
    data: CustomRoleCreate,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlatformAppService.create_custom_role(
        db, uuid.UUID(user["sub"]), org_id, data, request,
    )


@router.patch(
    "/organizations/{org_id}/custom-roles/{role_id}",
    response_model=AppRoleCatalogResponse,
)
async def update_org_custom_role(
    org_id: uuid.UUID,
    role_id: uuid.UUID,
    data: CustomRoleUpdate,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlatformAppService.update_custom_role(
        db, uuid.UUID(user["sub"]), org_id, role_id, data, request,
    )


@router.delete(
    "/organizations/{org_id}/custom-roles/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_org_custom_role(
    org_id: uuid.UUID,
    role_id: uuid.UUID,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await PlatformAppService.delete_custom_role(
        db, uuid.UUID(user["sub"]), org_id, role_id, request,
    )


# =====================================================================
# Organization apps (activate/deactivate per org)
# =====================================================================


@router.get(
    "/organizations/{org_id}/apps",
    response_model=list[OrgAppSummary],
)
async def list_org_apps(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlatformAppService.list_org_apps(db, org_id)


@router.post(
    "/organizations/{org_id}/apps/activate",
    response_model=OrgAppSummary,
    status_code=status.HTTP_201_CREATED,
)
async def activate_org_app(
    org_id: uuid.UUID,
    data: OrgAppActivateRequest,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await PlatformAppService.activate_org_app(
        db, uuid.UUID(user["sub"]), org_id, data.app_code, request,
    )
    apps = await PlatformAppService.list_org_apps(db, org_id)
    match = next((a for a in apps if a["app_code"] == data.app_code), None)
    if match is None:
        raise RuntimeError("Activation not visible after write")  # pragma: no cover
    return match


@router.post(
    "/organizations/{org_id}/apps/deactivate",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def deactivate_org_app(
    org_id: uuid.UUID,
    data: OrgAppActivateRequest,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await PlatformAppService.deactivate_org_app(
        db, uuid.UUID(user["sub"]), org_id, data.app_code, request,
    )


# =====================================================================
# Organization members + per-app roles
# =====================================================================


@router.get(
    "/organizations/{org_id}/members",
    response_model=list[OrgMemberSummary],
)
async def list_org_members(
    org_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await PlatformAppService.list_org_members(db, org_id)


@router.post(
    "/organizations/{org_id}/members",
    response_model=OrgMemberSummary,
    status_code=status.HTTP_201_CREATED,
)
async def invite_org_member(
    org_id: uuid.UUID,
    data: InviteMemberRequest,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    await PlatformAppService.invite_member(
        db, uuid.UUID(user["sub"]), org_id, data, request,
    )
    members = await PlatformAppService.list_org_members(db, org_id)
    return next(m for m in members if m["email"] == data.email)


@router.delete(
    "/organizations/{org_id}/members/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def remove_org_member(
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await PlatformAppService.remove_member(
        db, uuid.UUID(user["sub"]), org_id, user_id, request,
    )


@router.post(
    "/organizations/{org_id}/app-roles",
    status_code=status.HTTP_200_OK,
)
async def assign_org_app_role(
    org_id: uuid.UUID,
    data: AssignAppRoleRequest,
    request: Request,
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> Any:
    row = await PlatformAppService.assign_app_role(
        db, uuid.UUID(user["sub"]), org_id, data, request,
    )
    return {
        "id": str(row.id),
        "organization_id": str(row.organization_id),
        "user_id": str(row.user_id),
        "app_id": str(row.app_id),
        "role": row.role,
    }


@router.delete(
    "/organizations/{org_id}/app-roles",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def revoke_org_app_role(
    org_id: uuid.UUID,
    request: Request,
    user_id: uuid.UUID = Query(...),
    app_code: str = Query(...),
    user: dict = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
) -> None:
    await PlatformAppService.revoke_app_role(
        db, uuid.UUID(user["sub"]), org_id, user_id, app_code, request,
    )


# =====================================================================
# Audit log
# =====================================================================


@router.get("/audit", response_model=list[AuditLogEntry])
async def list_audit(
    actor_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    target_org_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
) -> Any:
    return await AuditService.list_entries(
        db, actor_id, action, target_org_id, limit,
    )
