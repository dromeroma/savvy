"""Pydantic schemas for condo residents."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

class ResidentCreate(BaseModel):
    unit_id: uuid.UUID; person_id: uuid.UUID
    resident_type: Literal["owner", "tenant", "family_member", "employee"] = "owner"
    is_primary: bool = False; move_in_date: date | None = None

class ResidentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; unit_id: uuid.UUID; person_id: uuid.UUID; resident_type: str
    is_primary: bool; move_in_date: date | None = None; status: str; created_at: datetime

class VisitorCreate(BaseModel):
    unit_id: uuid.UUID | None = None; visitor_name: str = Field(..., max_length=200)
    document_number: str | None = Field(None, max_length=50)
    vehicle_plate: str | None = Field(None, max_length=20)
    purpose: str | None = Field(None, max_length=100)
    authorized_by: str | None = Field(None, max_length=100)

class VisitorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; unit_id: uuid.UUID | None = None; visitor_name: str
    document_number: str | None = None; vehicle_plate: str | None = None
    purpose: str | None = None; entry_time: datetime; exit_time: datetime | None = None
    status: str; created_at: datetime
