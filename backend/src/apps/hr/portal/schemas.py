"""Schemas para el portal del empleado HR."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class PortalAuthRequest(BaseModel):
    org_slug: str = Field(..., min_length=1, max_length=100)
    employee_code: str = Field(..., min_length=1, max_length=40)
    document_number: str = Field(..., min_length=1, max_length=50)


class PortalEmployee(BaseModel):
    id: uuid.UUID
    organization_id: uuid.UUID
    employee_code: str
    first_name: str
    last_name: str | None = None
    email: str | None = None
    mobile: str | None = None
    address: str | None = None
    department_id: uuid.UUID | None = None
    department_name: str | None = None
    position_id: uuid.UUID | None = None
    position_name: str | None = None
    hire_date: date
    employment_type: str
    work_location: str
    status: str
    organization_name: str


class PortalAuthResponse(BaseModel):
    token: str
    expires_in_seconds: int
    employee: PortalEmployee


class PortalContractItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    contract_number: str
    contract_type: str
    start_date: date
    end_date: date | None = None
    base_salary: Decimal
    currency: str
    payment_frequency: str
    status: str
    eps_provider: str | None = None
    pension_provider: str | None = None


class PortalPayrollItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    period_id: uuid.UUID
    period_code: str
    period_name: str
    period_start: date
    period_end: date
    payment_date: date | None
    worked_days: Decimal
    total_earnings: Decimal
    total_deductions: Decimal
    net_amount: Decimal
    status: str
    paid_at: datetime | None = None


class PortalVacationBalance(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    period_year: int
    days_accrued: Decimal
    days_taken: Decimal
    days_pending: Decimal
    days_compensated: Decimal
    days_available: Decimal


class PortalVacationRequest(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    request_number: str
    request_type: str
    start_date: date
    end_date: date
    days_count: Decimal
    status: str
    request_reason: str | None = None
    rejection_reason: str | None = None
    requested_at: datetime
    approved_at: datetime | None = None


class PortalVacationRequestCreate(BaseModel):
    request_type: Literal["paid", "compensation", "unpaid"] = "paid"
    start_date: date
    end_date: date
    days_count: Decimal = Field(..., gt=0)
    request_reason: str | None = None


class PortalLeaveItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    leave_number: str
    leave_type: str
    subtype: str | None = None
    start_date: date
    end_date: date
    days_count: Decimal
    is_paid: bool
    paid_percentage: Decimal | None = None
    amount_paid: Decimal | None = None
    status: str


class PortalEvaluationItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    cycle_id: uuid.UUID
    cycle_name: str
    cycle_code: str
    cycle_period: str | None = None
    self_completed: bool
    supervisor_completed: bool
    overall_score: Decimal | None = None
    status: str
    completed_at: datetime | None = None


class PortalCompetency(BaseModel):
    code: str
    name: str
    weight: float | None = None
    description: str | None = None


class PortalEvaluationDetail(PortalEvaluationItem):
    competencies: list[PortalCompetency] = []
    scale_min: Decimal
    scale_max: Decimal
    enable_self: bool
    enable_supervisor: bool
    enable_360: bool


class PortalEvaluationResponseInput(BaseModel):
    evaluator_type: Literal["self", "peer", "subordinate"] = "self"
    scores: dict[str, float] = Field(default_factory=dict)
    comments: str | None = None


class PortalTrainingItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    course_id: uuid.UUID
    course_code: str
    course_name: str
    course_category: str
    duration_hours: Decimal | None = None
    scheduled_date: date | None = None
    completed_date: date | None = None
    completion_status: str
    score: Decimal | None = None
    certificate_url: str | None = None
    certificate_number: str | None = None


class PortalDocumentItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    document_type: str
    title: str
    description: str | None = None
    file_url: str | None = None
    issue_date: date | None = None
    expiration_date: date | None = None
    status: str


PortalAuthResponse.model_rebuild()
