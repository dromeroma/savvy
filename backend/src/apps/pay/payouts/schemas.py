"""Pydantic schemas for SavvyPay payouts."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class PayoutCreate(BaseModel):
    wallet_id: uuid.UUID
    amount: float = Field(..., gt=0)
    method: Literal["bank_transfer", "check", "cash", "mobile_payment"] = "bank_transfer"
    bank_details: dict[str, Any] = Field(default_factory=dict)
    scheduled_date: date | None = None
    idempotency_key: str | None = Field(None, max_length=100)

class PayoutResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; wallet_id: uuid.UUID; amount: float; fee: float; net_amount: float
    currency: str; method: str; scheduled_date: date | None = None
    executed_date: date | None = None; status: str; created_at: datetime
