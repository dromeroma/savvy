"""Schemas Pydantic para los catálogos de logística."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


VehicleType = Literal["hearse", "family", "utility", "other"]
VehicleStatus = Literal["active", "maintenance", "inactive"]
LocationKind = Literal["cemetery", "church", "other"]


# ---------------------------------------------------------------- Vehicles


class VehicleBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    plate: str = Field(..., min_length=1, max_length=20)
    brand: str | None = Field(None, max_length=60)
    model: str | None = Field(None, max_length=60)
    year: int | None = Field(None, ge=1900, le=2100)
    type: VehicleType = "hearse"
    capacity: int | None = Field(None, ge=1)
    color: str | None = Field(None, max_length=40)
    status: VehicleStatus = "active"
    default_driver_id: uuid.UUID | None = None
    notes: str | None = None


class VehicleCreate(VehicleBase):
    pass


class VehicleUpdate(BaseModel):
    plate: str | None = Field(None, max_length=20)
    brand: str | None = None
    model: str | None = None
    year: int | None = Field(None, ge=1900, le=2100)
    type: VehicleType | None = None
    capacity: int | None = Field(None, ge=1)
    color: str | None = None
    status: VehicleStatus | None = None
    default_driver_id: uuid.UUID | None = None
    notes: str | None = None


class VehicleResponse(VehicleBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- Drivers


class DriverBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    document_type: str | None = Field(None, max_length=10)
    document_number: str | None = Field(None, max_length=50)
    license_number: str | None = Field(None, max_length=50)
    license_category: str | None = Field(None, max_length=10)
    phone: str | None = Field(None, max_length=50)
    mobile: str | None = Field(None, max_length=50)
    email: EmailStr | None = None
    is_active: bool = True
    notes: str | None = None


class DriverCreate(DriverBase):
    pass


class DriverUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    license_number: str | None = None
    license_category: str | None = None
    phone: str | None = None
    mobile: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None
    notes: str | None = None


class DriverResponse(DriverBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- Rooms


class RoomBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=100)
    capacity: int | None = Field(None, ge=1)
    location: str | None = Field(None, max_length=255)
    is_active: bool = True
    notes: str | None = None


class RoomCreate(RoomBase):
    pass


class RoomUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    capacity: int | None = Field(None, ge=1)
    location: str | None = None
    is_active: bool | None = None
    notes: str | None = None


class RoomResponse(RoomBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- Ovens


class OvenBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=100)
    brand: str | None = Field(None, max_length=60)
    model: str | None = Field(None, max_length=60)
    daily_capacity: int | None = Field(None, ge=1)
    is_active: bool = True
    notes: str | None = None


class OvenCreate(OvenBase):
    pass


class OvenUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    brand: str | None = None
    model: str | None = None
    daily_capacity: int | None = Field(None, ge=1)
    is_active: bool | None = None
    notes: str | None = None


class OvenResponse(OvenBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- Locations


class LocationBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=255)
    kind: LocationKind
    address: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    contact_name: str | None = Field(None, max_length=150)
    contact_phone: str | None = Field(None, max_length=50)
    contact_email: EmailStr | None = None
    notes: str | None = None
    is_active: bool = True


class LocationCreate(LocationBase):
    pass


class LocationUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    address: str | None = None
    city: str | None = None
    contact_name: str | None = None
    contact_phone: str | None = None
    contact_email: EmailStr | None = None
    notes: str | None = None
    is_active: bool | None = None


class LocationResponse(LocationBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
