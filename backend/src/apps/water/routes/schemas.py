"""Pydantic schemas for water collection routes."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class RouteBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    collector_user_id: uuid.UUID | None = None
    is_active: bool = True


class RouteCreate(RouteBase):
    pass


class RouteUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = None
    collector_user_id: uuid.UUID | None = None
    is_active: bool | None = None


class RouteResponse(RouteBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class RouteListItem(BaseModel):
    """Route row with collector name + subscriber count + open balance."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    is_active: bool
    collector_user_id: uuid.UUID | None
    collector_name: str | None
    subscribers_count: int
    open_balance: Decimal


class RouteAssignmentCreate(BaseModel):
    subscriber_id: uuid.UUID
    sort_order: int = 0


class RouteAssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    route_id: uuid.UUID
    subscriber_id: uuid.UUID
    subscriber_code: str
    subscriber_name: str
    sort_order: int


# ---------- Collector mobile view ----------


class CollectorRouteSummary(BaseModel):
    route_id: uuid.UUID
    route_code: str
    route_name: str
    subscribers_count: int
    overdue_count: int
    open_balance: Decimal


class CollectorSubscriberItem(BaseModel):
    """Compact row for a collector's on-route view."""

    subscriber_id: uuid.UUID
    code: str
    name: str
    address: str | None
    mobile: str | None
    status: str
    sort_order: int
    open_balance: Decimal
    overdue_invoices: int
    oldest_due_date: str | None
