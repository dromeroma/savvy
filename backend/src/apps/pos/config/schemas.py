"""Pydantic schemas for POS config."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class TaxCreate(BaseModel):
    code: str = Field(..., max_length=30); name: str = Field(..., max_length=100)
    rate: float = Field(..., ge=0, le=1); is_inclusive: bool = False

class TaxResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; code: str; name: str; rate: float; is_inclusive: bool; status: str

class DiscountCreate(BaseModel):
    code: str = Field(..., max_length=30); name: str = Field(..., max_length=200)
    discount_type: Literal["percentage", "fixed"] = "percentage"
    value: float = Field(..., gt=0)
    min_amount: float = Field(0, ge=0)
    valid_from: date | None = None; valid_until: date | None = None

class DiscountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; code: str; name: str; discount_type: str; value: float
    min_amount: float; valid_from: date | None = None; valid_until: date | None = None; status: str
