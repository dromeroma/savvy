"""Pydantic schemas for water invoices."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class GenerateInvoiceRequest(BaseModel):
    """Generate a single invoice from a specific consumption reading."""

    consumption_id: uuid.UUID
    issue_date: date | None = None  # defaults to today
    due_date: date | None = None    # defaults to issue_date + 15 days
    surcharges: Decimal = Field(default=Decimal("0"), ge=0)
    discounts: Decimal = Field(default=Decimal("0"), ge=0)
    notes: str | None = None


class BatchGenerateRequest(BaseModel):
    """Generate invoices for every consumption in a given period that
    doesn't have an invoice yet."""

    period_year: int = Field(..., ge=2020, le=2100)
    period_month: int = Field(..., ge=1, le=12)
    issue_date: date | None = None
    due_date: date | None = None


class BatchGenerateResult(BaseModel):
    generated: int
    skipped_existing: int
    skipped_no_tariff: int
    errors: list[str] = []
    invoice_ids: list[uuid.UUID] = []


class InvoiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    subscriber_id: uuid.UUID
    consumption_id: uuid.UUID | None
    consecutive: int
    period_year: int
    period_month: int
    issue_date: date
    due_date: date
    fixed_charge: Decimal
    consumption_cubic: Decimal
    consumption_charge: Decimal
    late_interest: Decimal
    surcharges: Decimal
    discounts: Decimal
    reconnection_fee: Decimal
    suspension_fee: Decimal
    total: Decimal
    paid_amount: Decimal
    balance: Decimal
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class InvoiceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    consecutive: int
    period_year: int
    period_month: int
    issue_date: date
    due_date: date
    total: Decimal
    paid_amount: Decimal
    balance: Decimal
    status: str
    subscriber_id: uuid.UUID
    subscriber_code: str
    subscriber_name: str
