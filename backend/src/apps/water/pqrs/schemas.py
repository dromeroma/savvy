"""PQRS schemas (admin + customer views)."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


PqrsType = Literal["peticion", "queja", "reclamo", "sugerencia"]
PqrsStatus = Literal["open", "in_progress", "resolved", "closed"]


class PqrsCreate(BaseModel):
    """Created by a customer (subscriber_id is resolved from current user)."""
    type: PqrsType
    subject: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)


class AdminPqrsCreate(PqrsCreate):
    """Admin can also file PQRS on behalf of a subscriber."""
    subscriber_id: uuid.UUID


class PqrsRespond(BaseModel):
    response: str = Field(..., min_length=1)
    status: PqrsStatus = "resolved"


class PqrsStatusUpdate(BaseModel):
    status: PqrsStatus


class PqrsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    subscriber_id: uuid.UUID
    code: str
    type: str
    subject: str
    description: str
    status: str
    response: str | None
    responded_by: uuid.UUID | None
    responded_at: datetime | None
    created_by: uuid.UUID | None
    created_at: datetime
    updated_at: datetime


class PqrsListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    type: str
    subject: str
    status: str
    subscriber_id: uuid.UUID
    subscriber_code: str
    subscriber_name: str
    created_at: datetime
    responded_at: datetime | None
