"""Pydantic v2 schemas for SavvyEdu grading."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class EvaluationCreate(BaseModel):
    section_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=200)
    type: Literal["exam", "quiz", "assignment", "project", "participation"] = "exam"
    weight: float = Field(..., gt=0, le=1)
    max_score: float = Field(100, gt=0)
    due_date: date | None = None


class EvaluationUpdate(BaseModel):
    name: str | None = Field(None, max_length=200)
    weight: float | None = Field(None, gt=0, le=1)
    max_score: float | None = Field(None, gt=0)
    due_date: date | None = None
    status: Literal["active", "cancelled"] | None = None


class EvaluationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    section_id: uuid.UUID
    name: str
    type: str
    weight: float
    max_score: float
    due_date: date | None = None
    status: str
    created_at: datetime
    updated_at: datetime


class GradeCreate(BaseModel):
    evaluation_id: uuid.UUID
    student_id: uuid.UUID
    score: float = Field(..., ge=0)
    comments: str | None = None


class BulkGradeCreate(BaseModel):
    evaluation_id: uuid.UUID
    grades: list[GradeCreate] = Field(..., min_length=1)


class GradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    evaluation_id: uuid.UUID
    student_id: uuid.UUID
    score: float
    percentage: float | None = None
    comments: str | None = None
    graded_at: datetime | None = None
    created_at: datetime


class FinalGradeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    student_id: uuid.UUID
    section_id: uuid.UUID
    academic_period_id: uuid.UUID
    numeric_grade: float
    letter_grade: str | None = None
    gpa_points: float | None = None
    status: str
