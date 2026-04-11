"""Pydantic schemas for parking infrastructure."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field


class LocationCreate(BaseModel):
    code: str = Field(..., max_length=30)
    name: str = Field(..., max_length=200)
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    latitude: float | None = None
    longitude: float | None = None
    total_capacity: int = Field(0, ge=0)
    operating_hours: dict[str, Any] = Field(default_factory=dict)

class LocationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    name: str
    address: str | None = None
    city: str | None = None
    total_capacity: int
    current_occupancy: int
    operating_hours: dict[str, Any]
    status: str
    created_at: datetime

class ZoneCreate(BaseModel):
    location_id: uuid.UUID
    name: str = Field(..., max_length=100)
    zone_type: Literal["general", "vip", "handicapped", "motorcycle", "electric", "reserved"] = "general"
    level: str | None = Field(None, max_length=20)
    capacity: int = Field(0, ge=0)

class ZoneResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    location_id: uuid.UUID
    name: str
    zone_type: str
    level: str | None = None
    capacity: int
    current_occupancy: int

class SpotCreate(BaseModel):
    zone_id: uuid.UUID
    code: str = Field(..., max_length=20)
    spot_type: Literal["car", "motorcycle", "truck", "electric", "handicapped"] = "car"
    has_sensor: bool = False
    has_charger: bool = False

class SpotResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    zone_id: uuid.UUID
    code: str
    spot_type: str
    status: str
    has_sensor: bool
    has_charger: bool
