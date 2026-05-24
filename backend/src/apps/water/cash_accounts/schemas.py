"""Schemas for water cash accounts."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


CashAccountType = Literal["cash", "bank", "other"]


class CashAccountBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=100)
    type: CashAccountType = "cash"
    initial_balance: Decimal = Field(default=Decimal("0"))
    is_default: bool = False
    is_active: bool = True
    notes: str | None = None


class CashAccountCreate(CashAccountBase):
    pass


class CashAccountUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    type: CashAccountType | None = None
    initial_balance: Decimal | None = None
    is_default: bool | None = None
    is_active: bool | None = None
    notes: str | None = None


class CashAccountResponse(CashAccountBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class CashAccountListItem(BaseModel):
    """Cash account row with computed current balance."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    type: str
    is_default: bool
    is_active: bool
    initial_balance: Decimal
    current_balance: Decimal
    movement_count: int
