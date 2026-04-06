"""Pydantic v2 schemas for the SavvyFinance module."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


class CategoryCreate(BaseModel):
    """Payload to create a finance category."""

    app_code: str | None = None
    type: str = Field(..., pattern="^(income|expense)$")
    name: str = Field(..., max_length=100)
    code: str = Field(..., max_length=20)
    account_id: uuid.UUID | None = None


class CategoryResponse(BaseModel):
    """Public representation of a finance category."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    app_code: str | None = None
    type: str
    name: str
    code: str
    account_id: uuid.UUID | None = None
    is_system: bool
    created_at: datetime


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


class TransactionCreate(BaseModel):
    """Payload to create a finance transaction."""

    category_code: str = Field(..., max_length=20)
    type: str = Field(..., pattern="^(income|expense)$")
    person_id: uuid.UUID | None = None
    amount: Decimal = Field(..., gt=0, max_digits=15, decimal_places=2)
    date: date
    payment_method: str = Field(..., pattern="^(cash|transfer|card|check)$")
    description: str | None = None
    vendor: str | None = Field(default=None, max_length=255)
    app_code: str | None = None
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    scope_id: uuid.UUID | None = None


class TransactionResponse(BaseModel):
    """Public representation of a finance transaction."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    category_id: uuid.UUID
    type: str
    person_id: uuid.UUID | None = None
    amount: Decimal
    date: date
    payment_method: str
    description: str | None = None
    vendor: str | None = None
    receipt_url: str | None = None
    app_code: str | None = None
    reference_type: str | None = None
    reference_id: uuid.UUID | None = None
    scope_id: uuid.UUID | None = None
    fiscal_period_id: uuid.UUID | None = None
    journal_entry_id: uuid.UUID | None = None
    created_by: uuid.UUID
    created_at: datetime
    updated_at: datetime


class TransactionListParams(BaseModel):
    """Query parameters for listing transactions."""

    type: str | None = None
    app_code: str | None = None
    date_from: date | None = None
    date_to: date | None = None
    category_code: str | None = None
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


# ---------------------------------------------------------------------------
# Payment Accounts
# ---------------------------------------------------------------------------


class PaymentAccountCreate(BaseModel):
    """Payload to set a payment-method-to-account mapping."""

    payment_method: str = Field(..., pattern="^(cash|transfer|card|check)$")
    account_id: uuid.UUID


class PaymentAccountResponse(BaseModel):
    """Public representation of a payment account mapping."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    payment_method: str
    account_id: uuid.UUID
    created_at: datetime


# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------


class CategorySummaryLine(BaseModel):
    """Subtotal per category within a summary."""

    code: str
    name: str
    total: Decimal


class TransactionSummary(BaseModel):
    """Aggregated income/expense summary for a period."""

    total_income: Decimal
    total_expenses: Decimal
    net: Decimal
    by_category: list[CategorySummaryLine]
