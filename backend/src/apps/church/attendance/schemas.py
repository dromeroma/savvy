"""Pydantic schemas for church attendance."""

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class AttendanceRecord(BaseModel):
    person_id: uuid.UUID
    status: Literal["present", "absent", "late"] = "present"


class AttendanceBulkCreate(BaseModel):
    event_id: uuid.UUID
    records: list[AttendanceRecord]


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    event_id: uuid.UUID
    person_id: uuid.UUID
    status: str
    created_at: datetime


class AttendanceSummary(BaseModel):
    event_id: str
    event_name: str
    event_date: str
    total: int
    present: int
    absent: int
    late: int
