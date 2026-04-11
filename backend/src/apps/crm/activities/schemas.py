"""Pydantic schemas for CRM activities."""

from __future__ import annotations
import uuid
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field

ACTIVITY_TYPE = Literal["call", "meeting", "email", "task", "note"]

class ActivityCreate(BaseModel):
    type: ACTIVITY_TYPE
    subject: str = Field(..., min_length=1, max_length=200)
    description: str | None = None
    contact_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None
    due_date: date | None = None

class ActivityUpdate(BaseModel):
    subject: str | None = Field(None, max_length=200)
    description: str | None = None
    completed: bool | None = None
    due_date: date | None = None

class ActivityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    type: str
    subject: str
    description: str | None = None
    contact_id: uuid.UUID | None = None
    deal_id: uuid.UUID | None = None
    due_date: date | None = None
    completed: bool
    completed_at: datetime | None = None
    created_at: datetime
