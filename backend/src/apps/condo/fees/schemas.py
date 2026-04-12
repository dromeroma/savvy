"""Pydantic schemas for condo fees."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from pydantic import BaseModel, ConfigDict, Field

class FeeGenerate(BaseModel):
    property_id: uuid.UUID
    period: str = Field(..., pattern=r"^\d{4}-\d{2}$")  # 2026-04
    due_date: date

class FeePayment(BaseModel):
    amount: float = Field(..., gt=0)

class FeeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; unit_id: uuid.UUID; period: str; amount: float; late_fee: float; total: float
    due_date: date; paid_amount: float; paid_date: date | None = None; status: str
    description: str | None = None; created_at: datetime
