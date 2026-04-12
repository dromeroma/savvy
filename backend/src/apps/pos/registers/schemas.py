"""Pydantic schemas for POS cash registers."""

from __future__ import annotations
import uuid
from datetime import datetime
from pydantic import BaseModel, ConfigDict, Field

class RegisterOpen(BaseModel):
    location_id: uuid.UUID
    register_name: str = Field(..., max_length=100)
    opening_balance: float = Field(0, ge=0)

class RegisterClose(BaseModel):
    closing_balance: float = Field(..., ge=0)
    notes: str | None = None

class RegisterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; location_id: uuid.UUID; register_name: str
    opening_balance: float; opened_at: datetime | None = None
    closing_balance: float | None = None; expected_balance: float | None = None
    difference: float | None = None; closed_at: datetime | None = None
    status: str; notes: str | None = None
