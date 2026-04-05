"""Pydantic v2 schemas for the Accounting module."""

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Chart of Accounts
# ---------------------------------------------------------------------------


class AccountCreate(BaseModel):
    """Payload to create a new account in the chart of accounts."""

    code: str = Field(..., max_length=20)
    name: str = Field(..., max_length=255)
    type: str = Field(..., pattern="^(asset|liability|equity|revenue|expense)$")
    parent_id: uuid.UUID | None = None


class AccountUpdate(BaseModel):
    """Partial update payload for an account."""

    name: str | None = None
    is_active: bool | None = None


class AccountResponse(BaseModel):
    """Public representation of a chart-of-accounts entry."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    type: str
    parent_id: uuid.UUID | None = None
    is_active: bool
    is_system: bool


# ---------------------------------------------------------------------------
# Fiscal Periods
# ---------------------------------------------------------------------------


class FiscalPeriodCreate(BaseModel):
    """Payload to create a fiscal period."""

    year: int
    month: int = Field(..., ge=1, le=12)


class FiscalPeriodResponse(BaseModel):
    """Public representation of a fiscal period."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    year: int
    month: int
    start_date: date
    end_date: date
    status: str
    closed_at: datetime | None = None


# ---------------------------------------------------------------------------
# Journal Entries
# ---------------------------------------------------------------------------


class JournalEntryLineCreate(BaseModel):
    """A single debit/credit line when creating a journal entry."""

    account_code: str
    debit: Decimal = Decimal("0")
    credit: Decimal = Decimal("0")
    description: str | None = None


class JournalEntryLineResponse(BaseModel):
    """Public representation of a journal entry line."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    account_id: uuid.UUID
    account_code: str
    account_name: str
    debit: Decimal
    credit: Decimal
    description: str | None = None


class JournalEntryCreate(BaseModel):
    """Payload to create a manual journal entry."""

    date: date
    description: str = Field(..., max_length=500)
    lines: list[JournalEntryLineCreate] = Field(..., min_length=2)


class JournalEntryResponse(BaseModel):
    """Public representation of a journal entry with lines."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    entry_number: int
    date: date
    description: str
    source_app: str | None = None
    reference_type: str | None = None
    status: str
    lines: list[JournalEntryLineResponse]
    created_at: datetime


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


class ReportAccountLine(BaseModel):
    """A single account line within a financial report."""

    code: str
    name: str
    amount: Decimal


class IncomeStatementResponse(BaseModel):
    """Income statement (profit & loss) report."""

    revenues: list[ReportAccountLine]
    expenses: list[ReportAccountLine]
    total_revenue: Decimal
    total_expense: Decimal
    net_income: Decimal


class BalanceSheetResponse(BaseModel):
    """Balance sheet report."""

    assets: list[ReportAccountLine]
    liabilities: list[ReportAccountLine]
    equity: list[ReportAccountLine]
    total_assets: Decimal
    total_liabilities: Decimal
    total_equity: Decimal
