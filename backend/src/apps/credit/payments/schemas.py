"""Pydantic v2 schemas for SavvyCredit payments."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PaymentCreate(BaseModel):
    loan_id: uuid.UUID
    amount: float = Field(..., gt=0)
    payment_date: date | None = None
    method: Literal["cash", "bank_transfer", "check", "mobile_payment"] = "cash"
    notes: str | None = None


class PaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    loan_id: uuid.UUID
    amount: float
    principal_applied: float
    interest_applied: float
    penalty_applied: float
    payment_date: date
    method: str
    finance_transaction_id: uuid.UUID | None = None
    notes: str | None = None
    created_at: datetime


class PenaltyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    loan_id: uuid.UUID
    type: str
    amount: float
    applied_date: date
    status: str
    description: str | None = None
