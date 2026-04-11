"""Pydantic schemas for parking services."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class ServiceTypeCreate(BaseModel):
    name: str = Field(..., max_length=100)
    description: str | None = None
    price: float = Field(0, ge=0)
    category: Literal["wash", "valet", "detailing", "tire", "other"] = "wash"

class ServiceTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    name: str
    description: str | None = None
    price: float
    category: str
    status: str

class ServiceOrderCreate(BaseModel):
    service_id: uuid.UUID
    session_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    notes: str | None = None

class ServiceOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    session_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    service_id: uuid.UUID
    price: float
    status: str
    notes: str | None = None
    created_at: datetime
