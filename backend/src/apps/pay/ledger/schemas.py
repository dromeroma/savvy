"""Pydantic schemas for SavvyPay ledger."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

ACCOUNT_TYPE = Literal[
    "user_wallet", "user_pending", "user_reserved",
    "platform_fees", "platform_clearing", "platform_reserve", "external_bank",
]


class AccountCreate(BaseModel):
    code: str = Field(..., max_length=50)
    name: str = Field(..., max_length=200)
    account_type: ACCOUNT_TYPE
    currency: str = Field("COP", max_length=3)
    owner_person_id: uuid.UUID | None = None


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    name: str
    account_type: str
    currency: str
    owner_person_id: uuid.UUID | None = None
    is_active: bool
    created_at: datetime


class LedgerEntryLine(BaseModel):
    """A single line in a journal entry."""
    account_id: uuid.UUID
    entry_type: Literal["debit", "credit"]
    amount: float = Field(..., gt=0)
    description: str | None = None


class JournalCreate(BaseModel):
    """Create a balanced journal entry (multiple lines)."""
    lines: list[LedgerEntryLine] = Field(..., min_length=2)
    transaction_id: uuid.UUID | None = None
    source_app: str | None = Field(None, max_length=30)
    source_ref_type: str | None = Field(None, max_length=50)
    source_ref_id: uuid.UUID | None = None
    idempotency_key: str | None = Field(None, max_length=100)
    description: str | None = None


class LedgerEntryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    journal_id: uuid.UUID
    account_id: uuid.UUID
    entry_type: str
    amount: float
    currency: str
    description: str | None = None
    transaction_id: uuid.UUID | None = None
    source_app: str | None = None
    posted_at: datetime


class AccountBalanceResponse(BaseModel):
    account_id: uuid.UUID
    code: str
    name: str
    account_type: str
    currency: str
    balance: float


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    event_type: str
    entity_type: str
    entity_id: uuid.UUID
    data: dict[str, Any]
    source_app: str | None = None
    created_at: datetime
