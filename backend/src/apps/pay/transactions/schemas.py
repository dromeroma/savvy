"""Pydantic schemas for SavvyPay transactions."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

TX_TYPE = Literal["payment", "refund", "payout", "transfer", "subscription_charge"]
TX_STATUS = Literal["pending", "authorized", "captured", "settled", "failed", "refunded", "cancelled"]
PAY_METHOD = Literal["cash", "card", "bank_transfer", "wallet", "mobile_payment"]

class TransactionCreate(BaseModel):
    amount: float = Field(..., gt=0)
    currency: str = Field("COP", max_length=3)
    transaction_type: TX_TYPE = "payment"
    payment_method: PAY_METHOD | None = None
    payer_account_id: uuid.UUID | None = None
    payee_account_id: uuid.UUID | None = None
    source_app: str | None = Field(None, max_length=30)
    source_ref_type: str | None = Field(None, max_length=50)
    source_ref_id: uuid.UUID | None = None
    description: str | None = None
    idempotency_key: str | None = Field(None, max_length=100)
    metadata: dict[str, Any] = Field(default_factory=dict)

class TransactionAction(BaseModel):
    action: Literal["authorize", "capture", "settle", "fail", "cancel"]
    failure_reason: str | None = None

class RefundCreate(BaseModel):
    transaction_id: uuid.UUID
    amount: float = Field(..., gt=0)
    reason: str | None = Field(None, max_length=200)
    idempotency_key: str | None = Field(None, max_length=100)

class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; organization_id: uuid.UUID; idempotency_key: str | None = None
    transaction_type: str; amount: float; currency: str; fee_amount: float; net_amount: float
    payer_account_id: uuid.UUID | None = None; payee_account_id: uuid.UUID | None = None
    payment_method: str | None = None; status: str
    authorized_at: datetime | None = None; captured_at: datetime | None = None
    settled_at: datetime | None = None; failed_at: datetime | None = None
    failure_reason: str | None = None; refunded_amount: float
    source_app: str | None = None; description: str | None = None
    created_at: datetime; updated_at: datetime

class RefundResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; transaction_id: uuid.UUID; amount: float; reason: str | None = None
    status: str; processed_at: datetime | None = None; created_at: datetime
