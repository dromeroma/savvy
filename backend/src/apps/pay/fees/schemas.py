"""Pydantic schemas for SavvyPay fees."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class FeeRuleCreate(BaseModel):
    name: str = Field(..., max_length=100)
    fee_type: Literal["percentage", "fixed", "tiered"] = "percentage"
    percentage_value: float = Field(0, ge=0)
    fixed_value: float = Field(0, ge=0)
    min_fee: float = Field(0, ge=0)
    max_fee: float | None = Field(None, ge=0)
    applies_to: Literal["all", "payment", "payout", "subscription", "transfer"] = "all"
    source_app: str | None = Field(None, max_length=30)

class FeeRuleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; name: str; fee_type: str; percentage_value: float; fixed_value: float
    min_fee: float; max_fee: float | None = None; applies_to: str
    source_app: str | None = None; is_active: bool; created_at: datetime
