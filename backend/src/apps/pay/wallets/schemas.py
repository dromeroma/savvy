"""Pydantic schemas for SavvyPay wallets."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class WalletCreate(BaseModel):
    owner_person_id: uuid.UUID | None = None
    wallet_type: Literal["user", "merchant", "platform"] = "user"
    currency: str = Field("COP", max_length=3)

class WalletFund(BaseModel):
    amount: float = Field(..., gt=0)
    description: str | None = None
    idempotency_key: str | None = Field(None, max_length=100)

class WalletTransfer(BaseModel):
    to_wallet_id: uuid.UUID
    amount: float = Field(..., gt=0)
    description: str | None = None
    idempotency_key: str | None = Field(None, max_length=100)

class WalletResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; organization_id: uuid.UUID; owner_person_id: uuid.UUID | None = None
    wallet_type: str; currency: str; status: str; created_at: datetime

class WalletBalanceResponse(BaseModel):
    wallet_id: uuid.UUID
    wallet_type: str
    currency: str
    available: float
    pending: float
    reserved: float
    total: float
