"""Pydantic schemas for church events."""

import uuid
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


EVENT_TYPE = Literal["service", "event", "campaign", "meeting"]


class EventCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: EVENT_TYPE
    date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = Field(None, max_length=255)
    description: str | None = None
    is_recurring: bool = False
    expected_attendance: int | None = None


class EventUpdate(BaseModel):
    name: str | None = Field(None, max_length=255)
    type: EVENT_TYPE | None = None
    date: date | None = None
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = Field(None, max_length=255)
    description: str | None = None
    is_recurring: bool | None = None
    expected_attendance: int | None = None
    status: Literal["scheduled", "completed", "cancelled"] | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    type: str
    date: date
    start_time: time | None = None
    end_time: time | None = None
    location: str | None = None
    description: str | None = None
    is_recurring: bool
    expected_attendance: int | None = None
    status: str
    created_at: datetime
