"""Pydantic schemas for water payments."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PaymentMethod = Literal["cash", "transfer", "card", "check", "online"]


class PaymentAllocationInput(BaseModel):
    invoice_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)


class PaymentCreate(BaseModel):
    subscriber_id: uuid.UUID
    amount: Decimal = Field(..., gt=0)
    payment_date: date
    method: PaymentMethod = "cash"
    receipt_number: str | None = Field(None, max_length=40)
    reference: str | None = Field(None, max_length=100)
    notes: str | None = None
    # Cash account to credit. If null, uses the org's default account.
    cash_account_id: uuid.UUID | None = None
    # Optional explicit allocations. If empty, service auto-allocates to
    # the oldest pending invoices.
    allocations: list[PaymentAllocationInput] = []


class PaymentAllocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    invoice_id: uuid.UUID
    invoice_consecutive: int
    amount: Decimal


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    subscriber_id: uuid.UUID
    receipt_number: str | None
    payment_date: date
    amount: Decimal
    method: str
    reference: str | None
    notes: str | None
    collector_user_id: uuid.UUID | None
    cash_account_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime
    allocations: list[PaymentAllocationResponse] = []


class PaymentListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    payment_date: date
    amount: Decimal
    method: str
    receipt_number: str | None
    reference: str | None
    subscriber_id: uuid.UUID
    subscriber_code: str
    subscriber_name: str
    invoices_count: int
    cash_account_name: str | None = None
