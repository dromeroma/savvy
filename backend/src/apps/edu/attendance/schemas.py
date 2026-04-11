"""Pydantic v2 schemas for SavvyEdu attendance."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ATTENDANCE_STATUS = Literal["present", "absent", "late", "excused"]


class AttendanceRecord(BaseModel):
    student_id: uuid.UUID
    status: ATTENDANCE_STATUS = "present"
    notes: str | None = None


class BulkAttendanceCreate(BaseModel):
    section_id: uuid.UUID
    date: date
    records: list[AttendanceRecord] = Field(..., min_length=1)


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    section_id: uuid.UUID
    student_id: uuid.UUID
    date: date
    status: str
    notes: str | None = None
    created_at: datetime


class AttendanceSummary(BaseModel):
    section_id: uuid.UUID
    total_sessions: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_rate: float
