"""Pydantic v2 schemas for SavvyEdu configuration."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Grading System
# ---------------------------------------------------------------------------

GRADING_TYPES = Literal["numeric", "letter", "percentage"]


class GradeScaleCreate(BaseModel):
    label: str = Field(..., max_length=10)
    min_value: float
    max_value: float
    gpa_value: float | None = None
    is_passing: bool = True
    sort_order: int = 0


class GradeScaleResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    label: str
    min_value: float
    max_value: float
    gpa_value: float | None = None
    is_passing: bool
    sort_order: int


class GradingSystemCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    type: GRADING_TYPES
    scale_min: float = 0
    scale_max: float = 100
    passing_grade: float = 60
    is_default: bool = False
    scales: list[GradeScaleCreate] = Field(default_factory=list)


class GradingSystemUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    type: GRADING_TYPES | None = None
    scale_min: float | None = None
    scale_max: float | None = None
    passing_grade: float | None = None
    is_default: bool | None = None


class GradingSystemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    type: str
    scale_min: float
    scale_max: float
    passing_grade: float
    is_default: bool
    scales: list[GradeScaleResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Academic Period Type
# ---------------------------------------------------------------------------


class AcademicPeriodTypeCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=30)
    name: str = Field(..., min_length=1, max_length=100)
    default_duration_weeks: int = Field(16, ge=1, le=52)


class AcademicPeriodTypeUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    default_duration_weeks: int | None = Field(None, ge=1, le=52)


class AcademicPeriodTypeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    code: str
    name: str
    default_duration_weeks: int
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------------------
# Evaluation Template
# ---------------------------------------------------------------------------


class EvaluationComponentSchema(BaseModel):
    name: str = Field(..., max_length=100)
    weight: float = Field(..., gt=0, le=1)
    type: str = Field(..., max_length=30)  # exam, quiz, assignment, project, participation


class EvaluationTemplateCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = None
    components: list[EvaluationComponentSchema] = Field(..., min_length=1)
    is_default: bool = False


class EvaluationTemplateUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    description: str | None = None
    components: list[EvaluationComponentSchema] | None = None
    is_default: bool | None = None


class EvaluationTemplateResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    description: str | None = None
    components: list[dict[str, Any]]
    is_default: bool
    created_at: datetime
    updated_at: datetime
