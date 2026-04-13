"""Pydantic schemas for the platform module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# =====================================================================
# Platform roles
# =====================================================================


class PlatformRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    description: str | None = None
    is_active: bool
    created_at: datetime


class UserPlatformRoleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    user_id: uuid.UUID
    platform_role_id: uuid.UUID
    granted_by: uuid.UUID | None = None
    granted_at: datetime
    expires_at: datetime | None = None


class GrantRoleRequest(BaseModel):
    user_id: uuid.UUID
    role_code: str = Field(..., min_length=1, max_length=40)


# =====================================================================
# Plans
# =====================================================================


PLAN_STATUS = Literal["trial", "active", "past_due", "cancelled", "suspended"]
BILLING_CYCLE = Literal["monthly", "yearly"]


class PlanCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=100)
    tier: int = 0
    description: str | None = None
    price_monthly: Decimal = Field(default=Decimal("0"), ge=0)
    price_yearly: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field(default="USD", max_length=3)
    is_public: bool = True
    sort_order: int = 0


class PlanUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    tier: int | None = None
    description: str | None = None
    price_monthly: Decimal | None = Field(None, ge=0)
    price_yearly: Decimal | None = Field(None, ge=0)
    currency: str | None = Field(None, max_length=3)
    is_active: bool | None = None
    is_public: bool | None = None
    sort_order: int | None = None


class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    tier: int
    description: str | None = None
    price_monthly: Decimal
    price_yearly: Decimal
    currency: str
    is_active: bool
    is_public: bool
    sort_order: int
    created_at: datetime
    updated_at: datetime


# =====================================================================
# Features
# =====================================================================


FEATURE_TYPE = Literal["boolean", "quantity"]


class FeatureCreate(BaseModel):
    key: str = Field(..., min_length=1, max_length=60)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    category: str | None = Field(None, max_length=40)
    feature_type: FEATURE_TYPE
    default_enabled: bool | None = None
    default_limit: int | None = None


class FeatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    key: str
    name: str
    description: str | None = None
    category: str | None = None
    feature_type: str
    default_enabled: bool | None = None
    default_limit: int | None = None
    created_at: datetime


class PlanFeatureSet(BaseModel):
    feature_id: uuid.UUID
    enabled: bool = True
    limit_value: int | None = None


class PlanFeatureResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    plan_id: uuid.UUID
    feature_id: uuid.UUID
    enabled: bool
    limit_value: int | None = None


# =====================================================================
# Subscriptions
# =====================================================================


class SubscriptionCreate(BaseModel):
    organization_id: uuid.UUID
    plan_code: str = Field(..., min_length=1, max_length=40)
    status: PLAN_STATUS = "trial"
    billing_cycle: BILLING_CYCLE = "monthly"
    started_at: date | None = None
    expires_at: date | None = None
    trial_ends_at: date | None = None
    auto_renew: bool = True
    notes: str | None = None


class SubscriptionUpdate(BaseModel):
    plan_code: str | None = Field(None, max_length=40)
    status: PLAN_STATUS | None = None
    billing_cycle: BILLING_CYCLE | None = None
    started_at: date | None = None
    expires_at: date | None = None
    trial_ends_at: date | None = None
    auto_renew: bool | None = None
    notes: str | None = None


class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    plan_id: uuid.UUID
    status: str
    billing_cycle: str
    started_at: date
    expires_at: date | None = None
    trial_ends_at: date | None = None
    auto_renew: bool
    cancelled_at: datetime | None = None
    cancelled_by: uuid.UUID | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


# =====================================================================
# Organizations (admin view)
# =====================================================================


class PlatformOrgCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    slug: str = Field(..., min_length=2, max_length=100)
    type: Literal["business", "personal", "demo"] = "business"
    owner_email: EmailStr
    owner_name: str = Field(..., min_length=1, max_length=255)
    owner_password: str = Field(..., min_length=8, max_length=100)
    plan_code: str = Field(default="starter", max_length=40)
    trial_days: int = Field(default=14, ge=0, le=365)


class PlatformOrgUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    slug: str | None = Field(None, max_length=100)
    type: Literal["business", "personal", "demo", "platform"] | None = None


class PlatformOrgSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    type: str
    created_at: datetime
    member_count: int = 0
    subscription_status: str | None = None
    plan_name: str | None = None
    plan_code: str | None = None


class PlatformOrgDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    type: str
    settings: dict = {}
    created_at: datetime
    updated_at: datetime
    member_count: int = 0
    subscription: SubscriptionResponse | None = None
    plan_name: str | None = None


# =====================================================================
# Users (admin view)
# =====================================================================


class PlatformUserSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    email: str
    created_at: datetime
    last_login_at: datetime | None = None
    deleted_at: datetime | None = None
    organization_count: int = 0
    platform_roles: list[str] = []


# =====================================================================
# Feature overrides
# =====================================================================


class OverrideSet(BaseModel):
    feature_key: str = Field(..., min_length=1, max_length=60)
    enabled: bool | None = None
    limit_value: int | None = None
    reason: str | None = None
    expires_at: date | None = None


class OverrideResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    feature_id: uuid.UUID
    enabled: bool | None = None
    limit_value: int | None = None
    reason: str | None = None
    granted_by: uuid.UUID | None = None
    expires_at: date | None = None
    created_at: datetime
    updated_at: datetime


# =====================================================================
# Audit log
# =====================================================================


class AuditLogEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    actor_user_id: uuid.UUID | None = None
    action: str
    resource_type: str | None = None
    resource_id: uuid.UUID | None = None
    target_org_id: uuid.UUID | None = None
    payload: dict | None = None
    ip_address: str | None = None
    created_at: datetime


# =====================================================================
# Dashboard
# =====================================================================


class DashboardKPIs(BaseModel):
    total_organizations: int
    active_organizations: int
    trial_organizations: int
    suspended_organizations: int
    total_users: int
    mrr: Decimal
    new_orgs_last_30d: int
    cancelled_last_30d: int
    subscriptions_by_plan: dict[str, int]
