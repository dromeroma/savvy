"""Pydantic v2 schemas for SavvyEdu enrollment."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

SECTION_STATUS = Literal["open", "closed", "cancelled"]
ENROLLMENT_STATUS = Literal["enrolled", "dropped", "completed", "failed", "withdrawn"]


class SectionCreate(BaseModel):
    course_id: uuid.UUID
    academic_period_id: uuid.UUID
    teacher_id: uuid.UUID | None = None
    code: str = Field(..., min_length=1, max_length=30)
    capacity: int = Field(30, ge=1)


class SectionUpdate(BaseModel):
    teacher_id: uuid.UUID | None = None
    capacity: int | None = Field(None, ge=1)
    status: SECTION_STATUS | None = None


class SectionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    course_id: uuid.UUID
    academic_period_id: uuid.UUID
    teacher_id: uuid.UUID | None = None
    code: str
    capacity: int
    enrolled_count: int
    status: str
    created_at: datetime
    updated_at: datetime


class EnrollmentCreate(BaseModel):
    student_id: uuid.UUID
    section_id: uuid.UUID


class EnrollmentUpdate(BaseModel):
    status: ENROLLMENT_STATUS


class EnrollmentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    student_id: uuid.UUID
    section_id: uuid.UUID
    status: str
    enrolled_at: datetime
    created_at: datetime


class WaitlistResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    section_id: uuid.UUID
    position: int
