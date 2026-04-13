"""Pydantic schemas for rotations sub-module."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


ROTATION_TYPE = Literal[
    "ushers", "worship_team", "cleaning", "security", "kids", "welcome", "other",
]
FREQUENCY = Literal["weekly", "biweekly", "monthly", "event_based"]
ASSIGNMENT_STATUS = Literal["scheduled", "done", "swapped", "absent", "cancelled"]


class RotationCreate(BaseModel):
    scope_id: uuid.UUID | None = None
    name: str = Field(..., min_length=1, max_length=150)
    rotation_type: ROTATION_TYPE = "ushers"
    description: str | None = None
    frequency: FREQUENCY = "weekly"
    active: bool = True


class RotationUpdate(BaseModel):
    scope_id: uuid.UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=150)
    rotation_type: ROTATION_TYPE | None = None
    description: str | None = None
    frequency: FREQUENCY | None = None
    active: bool | None = None


class RotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    scope_id: uuid.UUID | None = None
    name: str
    rotation_type: str
    description: str | None = None
    frequency: str
    active: bool
    created_at: datetime
    updated_at: datetime


class AssignmentCreate(BaseModel):
    rotation_id: uuid.UUID
    person_id: uuid.UUID
    event_id: uuid.UUID | None = None
    assignment_date: date
    role: str | None = Field(None, max_length=60)
    status: ASSIGNMENT_STATUS = "scheduled"
    notes: str | None = None


class AssignmentUpdate(BaseModel):
    status: ASSIGNMENT_STATUS | None = None
    role: str | None = Field(None, max_length=60)
    notes: str | None = None


class AssignmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    rotation_id: uuid.UUID
    person_id: uuid.UUID
    event_id: uuid.UUID | None = None
    assignment_date: date
    role: str | None = None
    status: str
    notes: str | None = None
    created_at: datetime
    updated_at: datetime
