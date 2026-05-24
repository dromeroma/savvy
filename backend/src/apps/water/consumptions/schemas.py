"""Pydantic schemas for water consumption (lecturas mensuales)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class ConsumptionBase(BaseModel):
    meter_id: uuid.UUID
    period_year: int = Field(..., ge=2020, le=2100)
    period_month: int = Field(..., ge=1, le=12)
    reading_date: date
    current_reading: Decimal = Field(..., ge=0)
    is_estimated: bool = False
    notes: str | None = None


class ConsumptionCreate(ConsumptionBase):
    """`previous_reading` and `subscriber_id` are filled by the service
    from the meter's current state, so the client only sends the new reading."""


class ConsumptionUpdate(BaseModel):
    current_reading: Decimal | None = Field(None, ge=0)
    reading_date: date | None = None
    is_estimated: bool | None = None
    notes: str | None = None


class ConsumptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    meter_id: uuid.UUID
    subscriber_id: uuid.UUID
    period_year: int
    period_month: int
    reading_date: date
    previous_reading: Decimal
    current_reading: Decimal
    consumption_cubic: Decimal
    is_estimated: bool
    notes: str | None
    recorded_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class ConsumptionListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    period_year: int
    period_month: int
    reading_date: date
    previous_reading: Decimal
    current_reading: Decimal
    consumption_cubic: Decimal
    is_estimated: bool
    meter_id: uuid.UUID
    meter_serial: str
    subscriber_id: uuid.UUID
    subscriber_code: str
    subscriber_name: str
    has_invoice: bool
