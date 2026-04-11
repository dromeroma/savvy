"""Pydantic v2 schemas for SavvyEdu students."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


ACADEMIC_STATUS = Literal["active", "inactive", "graduated", "suspended", "expelled"]


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------


class StudentCreate(BaseModel):
    """Payload for creating a student (person + edu data)."""

    # Person fields
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    gender: Literal["male", "female"] | None = None
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=10)
    state: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)
    address: str | None = None

    # Student fields
    student_code: str = Field(..., min_length=1, max_length=30)
    program_id: uuid.UUID | None = None
    curriculum_version_id: uuid.UUID | None = None
    admission_date: date | None = None


# ---------------------------------------------------------------------------
# Update
# ---------------------------------------------------------------------------


class StudentUpdate(BaseModel):
    """Partial update for a student."""

    # Person fields
    first_name: str | None = Field(None, min_length=1, max_length=100)
    last_name: str | None = Field(None, min_length=1, max_length=100)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    date_of_birth: date | None = None
    gender: Literal["male", "female"] | None = None
    document_type: str | None = Field(None, max_length=20)
    document_number: str | None = Field(None, max_length=50)
    country: str | None = Field(None, max_length=10)
    state: str | None = Field(None, max_length=100)
    city: str | None = Field(None, max_length=100)
    address: str | None = None

    # Student fields
    program_id: uuid.UUID | None = None
    curriculum_version_id: uuid.UUID | None = None
    current_period_id: uuid.UUID | None = None
    academic_status: ACADEMIC_STATUS | None = None


# ---------------------------------------------------------------------------
# Response
# ---------------------------------------------------------------------------


class StudentResponse(BaseModel):
    """Public representation combining person + student data."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    person_id: uuid.UUID

    # Person fields (flattened)
    first_name: str
    last_name: str
    email: str | None = None
    phone: str | None = None
    date_of_birth: date | None = None
    gender: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    country: str | None = None
    state: str | None = None
    city: str | None = None
    address: str | None = None
    photo_url: str | None = None
    status: str

    # Student fields
    student_code: str
    program_id: uuid.UUID | None = None
    curriculum_version_id: uuid.UUID | None = None
    current_period_id: uuid.UUID | None = None
    admission_date: date | None = None
    academic_status: str
    cumulative_gpa: float | None = None
    completed_credits: int

    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Guardian
# ---------------------------------------------------------------------------


class GuardianCreate(BaseModel):
    person_id: uuid.UUID
    relationship: str = Field(..., max_length=30)
    is_primary: bool = False


class GuardianResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    person_id: uuid.UUID
    student_id: uuid.UUID
    relationship: str
    is_primary: bool


# ---------------------------------------------------------------------------
# List params
# ---------------------------------------------------------------------------


class StudentListParams(BaseModel):
    search: str | None = None
    program_id: uuid.UUID | None = None
    academic_status: ACADEMIC_STATUS | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(50, ge=1, le=200)
