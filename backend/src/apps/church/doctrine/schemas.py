"""Pydantic schemas for doctrine sub-module."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# -----------------------------------------------------------------
# Doctrine groups
# -----------------------------------------------------------------

DOCTRINE_STATUS = Literal["active", "completed", "cancelled", "scheduled"]


class DoctrineGroupCreate(BaseModel):
    scope_id: uuid.UUID | None = None
    name: str = Field(..., min_length=1, max_length=150)
    teacher_person_id: uuid.UUID | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    meeting_day: str | None = Field(None, max_length=20)
    meeting_time: time | None = None
    location: str | None = Field(None, max_length=200)
    max_students: int | None = Field(None, ge=1)
    status: DOCTRINE_STATUS = "active"


class DoctrineGroupUpdate(BaseModel):
    scope_id: uuid.UUID | None = None
    name: str | None = Field(None, min_length=1, max_length=150)
    teacher_person_id: uuid.UUID | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    meeting_day: str | None = Field(None, max_length=20)
    meeting_time: time | None = None
    location: str | None = Field(None, max_length=200)
    max_students: int | None = Field(None, ge=1)
    status: DOCTRINE_STATUS | None = None


class DoctrineGroupResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    scope_id: uuid.UUID | None = None
    name: str
    teacher_person_id: uuid.UUID | None = None
    description: str | None = None
    start_date: date | None = None
    end_date: date | None = None
    meeting_day: str | None = None
    meeting_time: time | None = None
    location: str | None = None
    max_students: int | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------
# Enrollments
# -----------------------------------------------------------------

ENROLLMENT_RESULT = Literal["graduated", "baptized", "dropped", "transferred"]


class EnrollmentCreate(BaseModel):
    doctrine_group_id: uuid.UUID
    person_id: uuid.UUID
    enrolled_at: date | None = None
    notes: str | None = None


class EnrollmentUpdate(BaseModel):
    progress_pct: int | None = Field(None, ge=0, le=100)
    result: ENROLLMENT_RESULT | None = None
    result_date: date | None = None
    notes: str | None = None


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    doctrine_group_id: uuid.UUID
    person_id: uuid.UUID
    enrolled_at: date
    progress_pct: int
    result: str | None = None
    result_date: date | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


# -----------------------------------------------------------------
# Attendance
# -----------------------------------------------------------------


class DoctrineAttendanceCreate(BaseModel):
    doctrine_group_id: uuid.UUID
    person_id: uuid.UUID
    session_date: date
    present: bool = True
    notes: str | None = None


class DoctrineAttendanceBulkCreate(BaseModel):
    doctrine_group_id: uuid.UUID
    session_date: date
    entries: list[dict]  # [{person_id, present}]


class DoctrineAttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    doctrine_group_id: uuid.UUID
    person_id: uuid.UUID
    session_date: date
    present: bool
    notes: str | None = None
    created_at: datetime
