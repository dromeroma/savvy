"""Pydantic v2 schemas for SavvyEdu academic structure."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Academic Period
# ---------------------------------------------------------------------------

PERIOD_STATUS = Literal["planned", "active", "closed"]


class AcademicPeriodCreate(BaseModel):
    period_type_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=100)
    year: int = Field(..., ge=2000, le=2200)
    start_date: date
    end_date: date


class AcademicPeriodUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    start_date: date | None = None
    end_date: date | None = None
    status: PERIOD_STATUS | None = None


class AcademicPeriodResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    period_type_id: uuid.UUID
    name: str
    year: int
    start_date: date
    end_date: date
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Program
# ---------------------------------------------------------------------------


class ProgramCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=200)
    scope_id: uuid.UUID | None = None
    grading_system_id: uuid.UUID | None = None
    evaluation_template_id: uuid.UUID | None = None
    degree_type: str | None = Field(None, max_length=50)
    duration_periods: int | None = Field(None, ge=1)
    credits_required: int | None = Field(None, ge=0)
    description: str | None = None


class ProgramUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    scope_id: uuid.UUID | None = None
    grading_system_id: uuid.UUID | None = None
    evaluation_template_id: uuid.UUID | None = None
    degree_type: str | None = Field(None, max_length=50)
    duration_periods: int | None = Field(None, ge=1)
    credits_required: int | None = Field(None, ge=0)
    description: str | None = None
    status: Literal["active", "inactive"] | None = None


class ProgramResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    scope_id: uuid.UUID | None = None
    grading_system_id: uuid.UUID | None = None
    evaluation_template_id: uuid.UUID | None = None
    code: str
    name: str
    degree_type: str | None = None
    duration_periods: int | None = None
    credits_required: int | None = None
    description: str | None = None
    status: str
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Course
# ---------------------------------------------------------------------------


class PrerequisiteSchema(BaseModel):
    prerequisite_id: uuid.UUID
    min_grade: float | None = None


class PrerequisiteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    prerequisite_id: uuid.UUID
    min_grade: float | None = None


class CourseCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=200)
    program_id: uuid.UUID | None = None
    credits: int = Field(0, ge=0)
    weekly_hours: int = Field(0, ge=0)
    is_elective: bool = False
    description: str | None = None
    prerequisites: list[PrerequisiteSchema] = Field(default_factory=list)


class CourseUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    program_id: uuid.UUID | None = None
    credits: int | None = Field(None, ge=0)
    weekly_hours: int | None = Field(None, ge=0)
    is_elective: bool | None = None
    description: str | None = None
    status: Literal["active", "inactive"] | None = None


class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    program_id: uuid.UUID | None = None
    code: str
    name: str
    credits: int
    weekly_hours: int
    is_elective: bool
    description: str | None = None
    status: str
    prerequisites: list[PrerequisiteResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Curriculum Version
# ---------------------------------------------------------------------------


class CurriculumVersionCreate(BaseModel):
    program_id: uuid.UUID
    version: str = Field(..., max_length=20)
    effective_from: date
    course_map: dict[str, list[str]]  # period_number -> [course_codes]


class CurriculumVersionUpdate(BaseModel):
    course_map: dict[str, list[str]] | None = None
    is_active: bool | None = None


class CurriculumVersionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    program_id: uuid.UUID
    version: str
    effective_from: date
    course_map: dict[str, Any]
    is_active: bool
    created_at: datetime
    updated_at: datetime
