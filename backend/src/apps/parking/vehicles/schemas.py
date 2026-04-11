"""Pydantic schemas for parking vehicles."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class VehicleCreate(BaseModel):
    plate: str = Field(..., max_length=20)
    vehicle_type: Literal["car", "motorcycle", "truck", "electric", "bicycle"] = "car"
    brand: str | None = Field(None, max_length=50)
    model: str | None = Field(None, max_length=50)
    color: str | None = Field(None, max_length=30)
    owner_person_id: uuid.UUID | None = None

class VehicleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    plate: str
    vehicle_type: str
    brand: str | None = None
    model: str | None = None
    color: str | None = None
    owner_person_id: uuid.UUID | None = None
    subscription_id: uuid.UUID | None = None
    status: str
    created_at: datetime
