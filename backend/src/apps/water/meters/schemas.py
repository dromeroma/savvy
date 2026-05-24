"""Pydantic schemas for water meters."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


MeterStatus = Literal["active", "replaced", "damaged", "inactive"]


class MeterBase(BaseModel):
    subscriber_id: uuid.UUID | None = None
    serial_number: str = Field(..., min_length=1, max_length=60)
    brand: str | None = Field(None, max_length=60)
    model: str | None = Field(None, max_length=60)
    diameter: str | None = Field(None, max_length=20)
    install_date: date | None = None
    initial_reading: Decimal = Decimal("0")
    last_reading: Decimal = Decimal("0")
    last_reading_date: date | None = None
    status: MeterStatus = "active"
    location_notes: str | None = None


class MeterCreate(MeterBase):
    pass


class MeterUpdate(BaseModel):
    subscriber_id: uuid.UUID | None = None
    brand: str | None = None
    model: str | None = None
    diameter: str | None = None
    install_date: date | None = None
    initial_reading: Decimal | None = None
    last_reading: Decimal | None = None
    last_reading_date: date | None = None
    status: MeterStatus | None = None
    location_notes: str | None = None


class MeterResponse(MeterBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class MeterListItem(BaseModel):
    """Compact row for the meters list (with subscriber name resolved)."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    serial_number: str
    brand: str | None
    model: str | None
    diameter: str | None
    status: str
    last_reading: Decimal
    last_reading_date: date | None
    subscriber_id: uuid.UUID | None
    subscriber_code: str | None
    subscriber_name: str | None
