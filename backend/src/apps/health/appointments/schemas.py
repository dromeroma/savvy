"""Pydantic schemas for health appointments."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

APT_STATUS = Literal["scheduled", "confirmed", "in_progress", "completed", "cancelled", "no_show"]

class AppointmentCreate(BaseModel):
    patient_id: uuid.UUID; provider_id: uuid.UUID; service_id: uuid.UUID | None = None
    appointment_date: date; start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$"); duration_minutes: int = Field(30, ge=5)
    reason: str | None = Field(None, max_length=200)

class AppointmentUpdate(BaseModel):
    status: APT_STATUS | None = None; notes: str | None = None
    payment_status: Literal["pending", "paid", "insurance"] | None = None

class AppointmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID; patient_id: uuid.UUID; provider_id: uuid.UUID; service_id: uuid.UUID | None = None
    appointment_date: date; start_time: str; end_time: str; duration_minutes: int
    reason: str | None = None; notes: str | None = None; status: str
    amount: float; payment_status: str; created_at: datetime
