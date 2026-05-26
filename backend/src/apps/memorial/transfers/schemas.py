"""Schemas Pydantic para traslados."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TransferType = Literal[
    "pickup", "to_velation", "to_cremation",
    "to_burial", "to_mass", "family", "other",
]
TransferStatus = Literal["scheduled", "in_progress", "completed", "cancelled"]


class TransferBase(BaseModel):
    service_id: uuid.UUID | None = None
    transfer_type: TransferType
    vehicle_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None
    scheduled_at: datetime
    origin: str | None = Field(None, max_length=255)
    destination: str | None = Field(None, max_length=255)
    notes: str | None = None


class TransferCreate(TransferBase):
    pass


class TransferUpdate(BaseModel):
    transfer_type: TransferType | None = None
    vehicle_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None
    scheduled_at: datetime | None = None
    origin: str | None = None
    destination: str | None = None
    notes: str | None = None


class TransferResponse(TransferBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    consecutive: int
    started_at: datetime | None = None
    completed_at: datetime | None = None
    status: str
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class TransferListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    consecutive: int
    service_id: uuid.UUID | None
    service_code: str | None
    deceased_name: str | None
    transfer_type: str
    vehicle_id: uuid.UUID | None
    vehicle_label: str | None
    driver_id: uuid.UUID | None
    driver_name: str | None
    scheduled_at: datetime
    completed_at: datetime | None
    origin: str | None
    destination: str | None
    status: str


class TransferTransitionRequest(BaseModel):
    """Transición de estado: scheduled → in_progress → completed, o cancelled."""

    new_status: TransferStatus
