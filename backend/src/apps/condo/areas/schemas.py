"""Pydantic schemas for condo common areas."""

from __future__ import annotations
import uuid
from datetime import datetime
from typing import Any, Literal
from pydantic import BaseModel, ConfigDict, Field

class CommonAreaCreate(BaseModel):
    property_id: uuid.UUID; name: str = Field(..., max_length=100)
    area_type: Literal["social", "gym", "pool", "bbq", "meeting_room", "playground", "terrace", "other"] = "social"
    capacity: int | None = None; requires_reservation: bool = True; reservation_fee: float = 0

class CommonAreaResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; property_id: uuid.UUID; name: str; area_type: str; capacity: int | None = None
    requires_reservation: bool; reservation_fee: float; rules: dict[str, Any]; status: str

class ReservationCreate(BaseModel):
    area_id: uuid.UUID; unit_id: uuid.UUID | None = None
    reserved_from: datetime; reserved_until: datetime; guests: int = 0; notes: str | None = None

class ReservationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; area_id: uuid.UUID; unit_id: uuid.UUID | None = None
    reserved_from: datetime; reserved_until: datetime; guests: int; fee: float; status: str; created_at: datetime
