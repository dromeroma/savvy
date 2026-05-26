"""Schemas para reportes de cartera y mora."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel


class RecalcResult(BaseModel):
    invoices_marked_overdue: int
    invoices_with_interest_applied: int
    contracts_suspended: int
    total_interest_applied: Decimal


class AgingBucket(BaseModel):
    bucket: Literal["current", "0_30", "31_60", "61_90", "90_plus"]
    invoices: int
    balance: Decimal


class AgingReport(BaseModel):
    total_balance: Decimal
    buckets: list[AgingBucket]


class OverdueDebtor(BaseModel):
    contract_id: uuid.UUID | None
    service_id: uuid.UUID | None
    code: str          # contract code or service code
    name: str          # titular o familia
    phone: str | None
    email: str | None
    overdue_invoices: int
    oldest_due_date: str | None
    days_overdue: int
    total_balance: Decimal
