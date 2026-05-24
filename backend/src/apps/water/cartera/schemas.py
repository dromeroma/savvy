"""Pydantic schemas for cartera (overdue management)."""

from __future__ import annotations

import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class RecalcResult(BaseModel):
    invoices_marked_overdue: int
    invoices_with_interest_applied: int
    subscribers_marked_overdue: int
    subscribers_recovered: int
    total_interest_applied: Decimal


class AgingBucket(BaseModel):
    bucket: str   # "0_30", "31_60", "61_90", "90_plus"
    invoices: int
    balance: Decimal


class AgingReport(BaseModel):
    total_balance: Decimal
    buckets: list[AgingBucket]


class OverdueSubscriber(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    subscriber_id: uuid.UUID
    code: str
    name: str
    phone: str | None
    mobile: str | None
    status: str
    overdue_invoices: int
    oldest_due_date: str | None  # ISO date
    days_overdue: int
    total_balance: Decimal
