"""Schemas for water treasury (movements + closings + balance)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MovementType = Literal["income", "expense"]


# Common categories for the picker; backend doesn't restrict the value
DEFAULT_CATEGORIES = {
    "income": ["water_payment", "other_income", "reconnection", "donation"],
    "expense": ["salary", "utility", "maintenance", "office", "transport", "tax", "other"],
}


class MovementBase(BaseModel):
    cash_account_id: uuid.UUID
    movement_date: date
    type: MovementType
    category: str | None = Field(None, max_length=60)
    amount: Decimal = Field(..., gt=0)
    description: str = Field(..., min_length=1)
    reference: str | None = Field(None, max_length=100)


class MovementCreate(MovementBase):
    pass


class MovementResponse(MovementBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    payment_id: uuid.UUID | None
    recorded_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class MovementListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    movement_date: date
    type: str
    category: str | None
    amount: Decimal
    description: str
    reference: str | None
    cash_account_id: uuid.UUID
    cash_account_name: str
    payment_id: uuid.UUID | None


# ---------- Closings (arqueos) ----------


class ClosingPreview(BaseModel):
    """Preview of the expected balance for an arqueo on a given date."""

    cash_account_id: uuid.UUID
    closing_date: date
    initial_balance: Decimal
    movements_income: Decimal
    movements_expense: Decimal
    expected_balance: Decimal


class ClosingCreate(BaseModel):
    cash_account_id: uuid.UUID
    closing_date: date
    counted_balance: Decimal
    notes: str | None = None


class ClosingResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    cash_account_id: uuid.UUID
    cash_account_name: str
    closing_date: date
    expected_balance: Decimal
    counted_balance: Decimal
    difference: Decimal
    notes: str | None
    closed_by: uuid.UUID | None
    closed_at: datetime


# ---------- Treasury dashboard ----------


class CashAccountBalance(BaseModel):
    cash_account_id: uuid.UUID
    code: str
    name: str
    type: str
    current_balance: Decimal


class TreasuryDashboard(BaseModel):
    total_balance: Decimal
    income_today: Decimal
    expense_today: Decimal
    income_this_month: Decimal
    expense_this_month: Decimal
    net_this_month: Decimal
    balances: list[CashAccountBalance]
