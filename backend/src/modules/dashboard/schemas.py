"""Pydantic schemas for the org-level dashboard summary."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class DashboardOrganization(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    slug: str
    type: str
    business_type: str | None = None
    business_type_label: str | None = None
    denomination_name: str | None = None
    zone_label: str | None = None
    member_count: int
    created_at: datetime


class DashboardSubscription(BaseModel):
    plan_code: str
    plan_name: str
    status: str
    billing_cycle: str
    started_at: str  # ISO date
    trial_ends_at: str | None = None


class DashboardApp(BaseModel):
    code: str
    name: str
    description: str | None = None
    icon: str | None = None
    color: str | None = None
    status: str
    user_role: str | None = None


class DashboardMetric(BaseModel):
    """A KPI card shown on the dashboard."""

    key: str
    label: str
    value: str            # pre-formatted ("$ 1.500.000", "120", etc.)
    raw_value: float | None = None
    icon: str | None = None
    color: str | None = None
    app_code: str | None = None  # None for org-level metrics


class DashboardExecutiveTotals(BaseModel):
    """Agregados cross-app del mes actual."""

    income_month: str  # "$ 45.230.000"
    income_month_raw: float
    receivables_total: str  # cartera por cobrar
    receivables_total_raw: float
    alerts_count: int  # número total de alertas críticas
    active_apps_count: int


class DashboardSummaryResponse(BaseModel):
    organization: DashboardOrganization
    subscription: DashboardSubscription | None
    active_apps: list[DashboardApp]
    metrics: list[DashboardMetric]
    totals: DashboardExecutiveTotals | None = None
