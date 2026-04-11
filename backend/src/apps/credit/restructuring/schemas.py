"""Pydantic v2 schemas for SavvyCredit restructuring."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RestructuringCreate(BaseModel):
    original_loan_id: uuid.UUID
    type: Literal["refinancing", "rescheduling", "settlement", "write_off"]
    reason: str | None = None
    new_rate: float | None = Field(None, ge=0)
    new_term: int | None = Field(None, ge=1)
    discount_amount: float | None = Field(None, ge=0)
    effective_date: date | None = None


class RestructuringResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    original_loan_id: uuid.UUID
    new_loan_id: uuid.UUID | None = None
    type: str
    reason: str | None = None
    original_balance: float
    new_balance: float | None = None
    effective_date: date
    terms: dict[str, Any]
    status: str
    created_at: datetime
