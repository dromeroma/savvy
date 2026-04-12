"""Pydantic schemas for SavvyPay subscriptions."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class PlanCreate(BaseModel):
    name: str = Field(..., max_length=100); code: str = Field(..., max_length=30)
    amount: float = Field(..., gt=0); currency: str = Field("COP", max_length=3)
    billing_cycle: Literal["weekly", "monthly", "quarterly", "annual"] = "monthly"
    trial_days: int = Field(0, ge=0)

class PlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; name: str; code: str; amount: float; currency: str
    billing_cycle: str; trial_days: int; is_active: bool; created_at: datetime

class SubscriptionCreate(BaseModel):
    plan_id: uuid.UUID; wallet_id: uuid.UUID | None = None

class SubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; plan_id: uuid.UUID; wallet_id: uuid.UUID | None = None
    status: str; current_period_start: date | None = None; current_period_end: date | None = None
    next_billing_date: date | None = None; created_at: datetime
