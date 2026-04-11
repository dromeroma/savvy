"""Pydantic schemas for parking sessions."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class SessionEntryCreate(BaseModel):
    location_id: uuid.UUID
    plate: str = Field(..., max_length=20)
    vehicle_type: str = Field("car", max_length=20)
    spot_id: uuid.UUID | None = None
    entry_method: Literal["manual", "lpr", "qr", "rfid"] = "manual"

class SessionExitCreate(BaseModel):
    payment_method: Literal["cash", "card", "transfer", "subscription", "waived"] = "cash"

class SessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    location_id: uuid.UUID
    spot_id: uuid.UUID | None = None
    vehicle_id: uuid.UUID | None = None
    plate: str
    vehicle_type: str
    entry_time: datetime
    exit_time: datetime | None = None
    duration_minutes: int | None = None
    amount: float
    discount: float
    total: float
    payment_status: str
    payment_method: str | None = None
    entry_method: str
    exit_method: str | None = None
    status: str
    created_at: datetime

class ReservationCreate(BaseModel):
    location_id: uuid.UUID
    spot_id: uuid.UUID | None = None
    plate: str | None = Field(None, max_length=20)
    reserved_from: datetime
    reserved_until: datetime

class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    location_id: uuid.UUID
    spot_id: uuid.UUID | None = None
    plate: str | None = None
    reserved_from: datetime
    reserved_until: datetime
    status: str
    created_at: datetime
