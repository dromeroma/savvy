"""Pydantic schemas for health services."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class ServiceCreate(BaseModel):
    name: str = Field(..., max_length=200); code: str | None = Field(None, max_length=20)
    category: Literal["consultation", "procedure", "lab", "imaging", "therapy", "other"] = "consultation"
    price: float = Field(0, ge=0); duration_minutes: int = Field(30, ge=5); description: str | None = None

class ServiceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; name: str; code: str | None = None; category: str; price: float
    duration_minutes: int; description: str | None = None; status: str; created_at: datetime
