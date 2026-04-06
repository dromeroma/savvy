"""Pydantic v2 schemas for church finance.

These remain church-specific for the API contract.  Internally, the service
layer maps them to the shared SavvyFinance TransactionCreate schema.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Categories (read-only, pulled from finance_categories)
# ---------------------------------------------------------------------------


class IncomeCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    is_system: bool
    account_id: uuid.UUID | None = None


class ExpenseCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    code: str
    is_system: bool
    account_id: uuid.UUID | None = None


# ---------------------------------------------------------------------------
# Income
# ---------------------------------------------------------------------------

PAYMENT_METHODS = Literal["cash", "transfer", "card", "check"]


class IncomeCreate(BaseModel):
    """Payload for registering an income."""

    category_code: str = Field(..., description="Income category code (TITHE, OFFERING, etc.)")
    person_id: uuid.UUID | None = None
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    date: date
    payment_method: PAYMENT_METHODS
    description: str | None = None


class IncomeResponse(BaseModel):
    """Public representation of an income transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    category_id: uuid.UUID
    type: str = "income"
    person_id: uuid.UUID | None = None
    amount: Decimal
    date: date
    payment_method: str
    description: str | None = None
    app_code: str | None = None
    fiscal_period_id: uuid.UUID | None = None
    journal_entry_id: uuid.UUID | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Expense
# ---------------------------------------------------------------------------


class ExpenseCreate(BaseModel):
    """Payload for registering an expense."""

    category_code: str = Field(..., description="Expense category code")
    amount: Decimal = Field(..., gt=0, decimal_places=2)
    date: date
    payment_method: PAYMENT_METHODS
    description: str | None = None
    vendor: str | None = None


class ExpenseResponse(BaseModel):
    """Public representation of an expense transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    category_id: uuid.UUID
    type: str = "expense"
    person_id: uuid.UUID | None = None
    amount: Decimal
    date: date
    payment_method: str
    description: str | None = None
    vendor: str | None = None
    receipt_url: str | None = None
    app_code: str | None = None
    fiscal_period_id: uuid.UUID | None = None
    journal_entry_id: uuid.UUID | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
