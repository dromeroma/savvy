"""Pydantic schemas for condo properties."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class PropertyCreate(BaseModel):
    code: str = Field(..., max_length=30)
    name: str = Field(..., max_length=200)
    property_type: Literal["residential", "commercial", "mixed", "office"] = "residential"
    address: str | None = None
    city: str | None = Field(None, max_length=100)
    total_units: int = Field(0, ge=0)
    admin_fee_base: float = Field(0, ge=0)
    late_fee_type: Literal["percentage", "fixed", "none"] = "percentage"
    late_fee_value: float = Field(0, ge=0)
    grace_days: int = Field(10, ge=0)

class PropertyResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    code: str; name: str; property_type: str; address: str | None = None; city: str | None = None
    total_units: int; admin_fee_base: float; late_fee_type: str; late_fee_value: float; grace_days: int
    status: str; created_at: datetime

class UnitCreate(BaseModel):
    property_id: uuid.UUID
    code: str = Field(..., max_length=20)
    unit_type: Literal["apartment", "office", "commercial", "parking", "storage"] = "apartment"
    floor: str | None = Field(None, max_length=10)
    area_sqm: float | None = Field(None, ge=0)
    coefficient: float = Field(1.0, gt=0)
    bedrooms: int | None = Field(None, ge=0)
    bathrooms: int | None = Field(None, ge=0)
    owner_person_id: uuid.UUID | None = None

class UnitResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; property_id: uuid.UUID; code: str; unit_type: str; floor: str | None = None
    area_sqm: float | None = None; coefficient: float; bedrooms: int | None = None; bathrooms: int | None = None
    owner_person_id: uuid.UUID | None = None; status: str; created_at: datetime
