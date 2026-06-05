"""Schemas Pydantic para SavvyHR fase 1."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================ enums

EmployeeStatus = Literal["active", "on_leave", "suspended", "terminated"]
EmploymentType = Literal["full_time", "part_time", "intern", "contractor", "temporary"]
WorkLocation = Literal["onsite", "remote", "hybrid"]

ContractType = Literal[
    "indefinido", "fijo", "obra_labor", "prestacion", "aprendiz", "practicante", "otro",
]
PaymentFrequency = Literal["monthly", "biweekly", "weekly"]
ContractStatus = Literal["draft", "active", "suspended", "terminated", "expired"]

DocumentType = Literal[
    "resume", "contract", "id_copy", "tax_id",
    "eps_affiliation", "pension_affiliation", "severance_affiliation",
    "arl_affiliation", "compensation_fund_affiliation",
    "medical_exam", "background_check", "study_certificate", "work_certificate",
    "training_certificate", "disciplinary_record", "other",
]
DocumentStatus = Literal["valid", "expired", "revoked", "pending_review"]


# ============================================================ Department


class DepartmentBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    cost_center: str | None = Field(None, max_length=40)
    parent_id: uuid.UUID | None = None
    manager_employee_id: uuid.UUID | None = None
    is_active: bool = True


class DepartmentCreate(DepartmentBase):
    pass


class DepartmentUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    description: str | None = None
    cost_center: str | None = Field(None, max_length=40)
    parent_id: uuid.UUID | None = None
    manager_employee_id: uuid.UUID | None = None
    is_active: bool | None = None


class DepartmentResponse(DepartmentBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ============================================================ Position


class PositionBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    department_id: uuid.UUID | None = None
    level: int | None = Field(None, ge=1, le=20)
    min_salary: Decimal | None = Field(None, ge=0)
    max_salary: Decimal | None = Field(None, ge=0)
    reference_salary: Decimal | None = Field(None, ge=0)
    currency: str = Field("COP", min_length=3, max_length=3)
    headcount_budget: int | None = Field(None, ge=0)
    is_active: bool = True


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    description: str | None = None
    department_id: uuid.UUID | None = None
    level: int | None = Field(None, ge=1, le=20)
    min_salary: Decimal | None = Field(None, ge=0)
    max_salary: Decimal | None = Field(None, ge=0)
    reference_salary: Decimal | None = Field(None, ge=0)
    currency: str | None = Field(None, min_length=3, max_length=3)
    headcount_budget: int | None = Field(None, ge=0)
    is_active: bool | None = None


class PositionResponse(PositionBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ============================================================ Employee


class EmployeeBase(BaseModel):
    employee_code: str = Field(..., min_length=1, max_length=40)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    document_type: str | None = Field(None, max_length=10)
    document_number: str | None = Field(None, max_length=50)
    birth_date: date | None = None
    gender: str | None = Field(None, max_length=10)
    marital_status: str | None = Field(None, max_length=20)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    mobile: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=255)
    city: str | None = Field(None, max_length=100)
    country_code: str | None = Field(None, min_length=2, max_length=3)
    emergency_contact_name: str | None = Field(None, max_length=150)
    emergency_contact_phone: str | None = Field(None, max_length=50)
    emergency_contact_relationship: str | None = Field(None, max_length=40)
    department_id: uuid.UUID | None = None
    position_id: uuid.UUID | None = None
    supervisor_id: uuid.UUID | None = None
    hire_date: date
    employment_type: EmploymentType = "full_time"
    work_location: WorkLocation = "onsite"
    user_id: uuid.UUID | None = None
    person_id: uuid.UUID | None = None
    notes: str | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    document_type: str | None = Field(None, max_length=10)
    document_number: str | None = Field(None, max_length=50)
    birth_date: date | None = None
    gender: str | None = None
    marital_status: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    mobile: str | None = None
    address: str | None = None
    city: str | None = None
    country_code: str | None = None
    emergency_contact_name: str | None = None
    emergency_contact_phone: str | None = None
    emergency_contact_relationship: str | None = None
    department_id: uuid.UUID | None = None
    position_id: uuid.UUID | None = None
    supervisor_id: uuid.UUID | None = None
    status: EmployeeStatus | None = None
    employment_type: EmploymentType | None = None
    work_location: WorkLocation | None = None
    termination_date: date | None = None
    termination_reason: str | None = None
    user_id: uuid.UUID | None = None
    notes: str | None = None


class EmployeeResponse(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    status: EmployeeStatus
    termination_date: date | None = None
    termination_reason: str | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class EmployeeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    employee_code: str
    first_name: str
    last_name: str | None = None
    document_number: str | None = None
    email: str | None = None
    mobile: str | None = None
    department_id: uuid.UUID | None = None
    department_name: str | None = None
    position_id: uuid.UUID | None = None
    position_name: str | None = None
    hire_date: date
    status: EmployeeStatus
    employment_type: EmploymentType


# ============================================================ Contract


class ContractBase(BaseModel):
    contract_number: str = Field(..., min_length=1, max_length=40)
    contract_type: ContractType
    start_date: date
    end_date: date | None = None
    trial_period_end: date | None = None
    base_salary: Decimal = Field(default=Decimal("0"), ge=0)
    currency: str = Field("COP", min_length=3, max_length=3)
    payment_frequency: PaymentFrequency = "monthly"
    weekly_hours: Decimal = Field(default=Decimal("48"), ge=0, le=168)
    transport_allowance: Decimal = Field(default=Decimal("0"), ge=0)
    food_allowance: Decimal = Field(default=Decimal("0"), ge=0)
    connectivity_allowance: Decimal = Field(default=Decimal("0"), ge=0)
    other_allowance: Decimal = Field(default=Decimal("0"), ge=0)
    risk_class: str | None = Field(None, max_length=10)
    eps_provider: str | None = Field(None, max_length=150)
    pension_provider: str | None = Field(None, max_length=150)
    severance_provider: str | None = Field(None, max_length=150)
    compensation_fund: str | None = Field(None, max_length=150)
    bank_name: str | None = Field(None, max_length=80)
    bank_account_type: str | None = Field(None, max_length=20)
    bank_account_number: str | None = Field(None, max_length=40)
    notes: str | None = None


class ContractCreate(ContractBase):
    employee_id: uuid.UUID


class ContractUpdate(BaseModel):
    end_date: date | None = None
    base_salary: Decimal | None = Field(None, ge=0)
    transport_allowance: Decimal | None = Field(None, ge=0)
    food_allowance: Decimal | None = Field(None, ge=0)
    connectivity_allowance: Decimal | None = Field(None, ge=0)
    other_allowance: Decimal | None = Field(None, ge=0)
    payment_frequency: PaymentFrequency | None = None
    weekly_hours: Decimal | None = Field(None, ge=0, le=168)
    risk_class: str | None = None
    eps_provider: str | None = None
    pension_provider: str | None = None
    severance_provider: str | None = None
    compensation_fund: str | None = None
    bank_name: str | None = None
    bank_account_type: str | None = None
    bank_account_number: str | None = None
    status: ContractStatus | None = None
    termination_reason: str | None = None
    notes: str | None = None


class ContractResponse(ContractBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    employee_id: uuid.UUID
    renewal_count: int
    status: ContractStatus
    terminated_at: datetime | None = None
    termination_reason: str | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================ Document


class DocumentBase(BaseModel):
    document_type: DocumentType
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    file_url: str | None = None
    file_size_bytes: int | None = Field(None, ge=0)
    issue_date: date | None = None
    expiration_date: date | None = None
    issuer: str | None = Field(None, max_length=150)
    reference_code: str | None = Field(None, max_length=100)


class DocumentCreate(DocumentBase):
    employee_id: uuid.UUID


class DocumentUpdate(BaseModel):
    title: str | None = Field(None, max_length=255)
    description: str | None = None
    file_url: str | None = None
    file_size_bytes: int | None = Field(None, ge=0)
    issue_date: date | None = None
    expiration_date: date | None = None
    issuer: str | None = None
    reference_code: str | None = None
    status: DocumentStatus | None = None


class DocumentResponse(DocumentBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    employee_id: uuid.UUID
    status: DocumentStatus
    uploaded_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime
