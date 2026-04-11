"""Pydantic v2 schemas for SavvyEdu scheduling."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class RoomCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    building: str | None = Field(None, max_length=100)
    floor: str | None = Field(None, max_length=20)
    capacity: int = Field(30, ge=1)
    type: Literal["classroom", "lab", "auditorium", "virtual"] = "classroom"
    equipment: list[str] | None = None
    scope_id: uuid.UUID | None = None


class RoomUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    building: str | None = Field(None, max_length=100)
    floor: str | None = Field(None, max_length=20)
    capacity: int | None = Field(None, ge=1)
    type: Literal["classroom", "lab", "auditorium", "virtual"] | None = None
    equipment: list[str] | None = None
    status: Literal["active", "inactive"] | None = None


class RoomResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    scope_id: uuid.UUID | None = None
    name: str
    building: str | None = None
    floor: str | None = None
    capacity: int
    type: str
    equipment: Any = None
    status: str
    created_at: datetime
    updated_at: datetime


class ScheduleCreate(BaseModel):
    section_id: uuid.UUID
    room_id: uuid.UUID | None = None
    day_of_week: int = Field(..., ge=0, le=6)
    start_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")
    end_time: str = Field(..., pattern=r"^\d{2}:\d{2}$")


class ScheduleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    section_id: uuid.UUID
    room_id: uuid.UUID | None = None
    day_of_week: int
    start_time: str
    end_time: str
    created_at: datetime
    updated_at: datetime
