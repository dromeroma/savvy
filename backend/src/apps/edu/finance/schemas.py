"""Pydantic v2 schemas for SavvyEdu finance."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class InstallmentSchema(BaseModel):
    due_date: date
    amount: float = Field(..., gt=0)


class TuitionPlanCreate(BaseModel):
    program_id: uuid.UUID
    academic_period_id: uuid.UUID
    name: str = Field(..., min_length=1, max_length=100)
    total_amount: float = Field(..., gt=0)
    installments: list[InstallmentSchema] = Field(default_factory=list)


class TuitionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    program_id: uuid.UUID
    academic_period_id: uuid.UUID
    name: str
    total_amount: float
    installments: list[dict[str, Any]]
    created_at: datetime
    updated_at: datetime


class StudentChargeCreate(BaseModel):
    student_id: uuid.UUID
    tuition_plan_id: uuid.UUID | None = None
    description: str = Field(..., max_length=200)
    amount: float = Field(..., gt=0)
    due_date: date | None = None


class StudentChargeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    student_id: uuid.UUID
    tuition_plan_id: uuid.UUID | None = None
    description: str
    amount: float
    balance: float
    due_date: date | None = None
    status: str
    created_at: datetime


class ScholarshipCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    type: Literal["percentage", "fixed"] = "percentage"
    value: float = Field(..., gt=0)
    academic_period_id: uuid.UUID | None = None


class ScholarshipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    organization_id: uuid.UUID
    name: str
    type: str
    value: float
    academic_period_id: uuid.UUID | None = None
    status: str
    created_at: datetime


class ScholarshipAwardCreate(BaseModel):
    scholarship_id: uuid.UUID
    student_id: uuid.UUID
    applied_amount: float = Field(..., gt=0)
    academic_period_id: uuid.UUID | None = None


class ScholarshipAwardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    scholarship_id: uuid.UUID
    student_id: uuid.UUID
    applied_amount: float
    academic_period_id: uuid.UUID | None = None
