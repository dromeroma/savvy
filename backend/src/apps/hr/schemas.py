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


# ============================================================ Fase 2 — Shifts

from datetime import time as _time  # noqa: E402

ShiftType = Literal["morning", "afternoon", "night", "rotating", "flexible", "administrative"]


class ShiftBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    shift_type: ShiftType = "morning"
    start_time: _time | None = None
    end_time: _time | None = None
    break_minutes: int = Field(default=0, ge=0, le=480)
    days_of_week: list[int] = Field(default_factory=lambda: [1, 2, 3, 4, 5])
    weekly_hours: Decimal | None = Field(None, ge=0, le=168)
    is_active: bool = True


class ShiftCreate(ShiftBase):
    pass


class ShiftUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    description: str | None = None
    shift_type: ShiftType | None = None
    start_time: _time | None = None
    end_time: _time | None = None
    break_minutes: int | None = Field(None, ge=0, le=480)
    days_of_week: list[int] | None = None
    weekly_hours: Decimal | None = None
    is_active: bool | None = None


class ShiftResponse(ShiftBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ============================================================ Fase 2 — Attendance

AttendanceStatus = Literal[
    "present", "absent", "late", "early_leave", "justified",
    "vacation", "sick_leave", "permit", "holiday",
]


class AttendanceBase(BaseModel):
    employee_id: uuid.UUID
    work_date: date
    shift_id: uuid.UUID | None = None
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    planned_hours: Decimal | None = Field(None, ge=0, le=24)
    worked_hours: Decimal | None = Field(None, ge=0, le=24)
    overtime_day_hours: Decimal = Field(default=Decimal("0"), ge=0, le=24)
    overtime_night_hours: Decimal = Field(default=Decimal("0"), ge=0, le=24)
    overtime_holiday_hours: Decimal = Field(default=Decimal("0"), ge=0, le=24)
    status: AttendanceStatus = "present"
    notes: str | None = None


class AttendanceCreate(AttendanceBase):
    pass


class AttendanceUpdate(BaseModel):
    shift_id: uuid.UUID | None = None
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    planned_hours: Decimal | None = None
    worked_hours: Decimal | None = None
    overtime_day_hours: Decimal | None = None
    overtime_night_hours: Decimal | None = None
    overtime_holiday_hours: Decimal | None = None
    status: AttendanceStatus | None = None
    notes: str | None = None


class AttendanceResponse(AttendanceBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    recorded_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class AttendanceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    employee_id: uuid.UUID
    employee_code: str
    employee_name: str
    work_date: date
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    worked_hours: Decimal | None = None
    overtime_total: Decimal = Decimal("0")
    status: AttendanceStatus


# ============================================================ Fase 2 — Vacations

VacationRequestType = Literal["paid", "compensation", "unpaid"]
VacationStatus = Literal["pending", "approved", "rejected", "cancelled", "completed"]


class VacationBalanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    employee_id: uuid.UUID
    period_year: int
    days_accrued: Decimal
    days_taken: Decimal
    days_pending: Decimal
    days_compensated: Decimal
    last_accrual_at: datetime | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class VacationBalanceAdjust(BaseModel):
    """Ajuste manual del saldo (carga inicial o corrección)."""
    period_year: int = Field(..., ge=2000, le=2100)
    days_accrued: Decimal | None = Field(None, ge=0)
    days_taken: Decimal | None = Field(None, ge=0)
    days_compensated: Decimal | None = Field(None, ge=0)
    notes: str | None = None


class VacationRequestBase(BaseModel):
    employee_id: uuid.UUID
    request_type: VacationRequestType = "paid"
    start_date: date
    end_date: date
    days_count: Decimal = Field(..., gt=0)
    request_reason: str | None = None
    compensation_amount: Decimal | None = Field(None, ge=0)
    notes: str | None = None


class VacationRequestCreate(VacationRequestBase):
    pass


class VacationRequestResponse(VacationRequestBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    request_number: str
    status: VacationStatus
    rejection_reason: str | None = None
    requested_at: datetime
    approved_at: datetime | None = None
    approved_by: uuid.UUID | None = None
    rejected_at: datetime | None = None
    rejected_by: uuid.UUID | None = None
    cancelled_at: datetime | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


class VacationApproval(BaseModel):
    notes: str | None = None


class VacationRejection(BaseModel):
    rejection_reason: str = Field(..., min_length=1, max_length=500)


# ============================================================ Fase 2 — Leaves

LeaveType = Literal[
    "medical", "maternity", "paternity", "bereavement",
    "unpaid", "paid_other", "study", "remunerated_permit",
]
LeaveStatus = Literal["active", "completed", "cancelled"]


class LeaveBase(BaseModel):
    employee_id: uuid.UUID
    leave_type: LeaveType
    subtype: str | None = Field(None, max_length=40)
    start_date: date
    end_date: date
    days_count: Decimal = Field(..., gt=0)
    is_paid: bool = True
    paid_percentage: Decimal | None = Field(None, ge=0, le=100)
    amount_paid: Decimal | None = Field(None, ge=0)
    supporting_doc_url: str | None = None
    supporting_doc_number: str | None = Field(None, max_length=80)
    supporting_doc_issuer: str | None = Field(None, max_length=150)
    diagnosis_code: str | None = Field(None, max_length=20)
    notes: str | None = None


class LeaveCreate(LeaveBase):
    pass


class LeaveUpdate(BaseModel):
    subtype: str | None = None
    end_date: date | None = None
    days_count: Decimal | None = None
    is_paid: bool | None = None
    paid_percentage: Decimal | None = None
    amount_paid: Decimal | None = None
    supporting_doc_url: str | None = None
    supporting_doc_number: str | None = None
    supporting_doc_issuer: str | None = None
    diagnosis_code: str | None = None
    status: LeaveStatus | None = None
    notes: str | None = None


class LeaveResponse(LeaveBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    leave_number: str
    status: LeaveStatus
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================ Fase 3 — Payroll concepts

ConceptType = Literal["earning", "deduction", "benefit", "employer_contribution", "informative"]
CalculationMethod = Literal["fixed", "percentage", "formula", "quantity_rate"]


class PayrollConceptBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    concept_type: ConceptType
    category: str = Field(..., min_length=1, max_length=40)
    calculation_method: CalculationMethod = "fixed"
    formula: str | None = None
    percentage_value: Decimal | None = Field(None, ge=0)
    fixed_value: Decimal | None = Field(None, ge=0)
    base_concept_code: str | None = Field(None, max_length=40)
    country_code: str | None = Field(None, max_length=3)
    is_taxable: bool = True
    is_active: bool = True
    sort_order: int = 100


class PayrollConceptCreate(PayrollConceptBase):
    pass


class PayrollConceptUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    percentage_value: Decimal | None = None
    fixed_value: Decimal | None = None
    base_concept_code: str | None = None
    formula: str | None = None
    is_taxable: bool | None = None
    is_active: bool | None = None
    sort_order: int | None = None


class PayrollConceptResponse(PayrollConceptBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ============================================================ Fase 3 — Payroll periods

PayrollPeriodType = Literal["monthly", "biweekly", "weekly"]
PayrollPeriodStatus = Literal[
    "draft", "calculating", "calculated", "approved", "paid", "closed", "cancelled",
]


class PayrollPeriodBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=150)
    period_type: PayrollPeriodType = "monthly"
    start_date: date
    end_date: date
    payment_date: date | None = None
    notes: str | None = None


class PayrollPeriodCreate(PayrollPeriodBase):
    pass


class PayrollPeriodUpdate(BaseModel):
    name: str | None = None
    payment_date: date | None = None
    notes: str | None = None


class PayrollPeriodResponse(PayrollPeriodBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    status: PayrollPeriodStatus
    total_gross: Decimal
    total_deductions: Decimal
    total_net: Decimal
    employee_count: int
    calculated_at: datetime | None = None
    approved_at: datetime | None = None
    approved_by: uuid.UUID | None = None
    paid_at: datetime | None = None
    paid_by: uuid.UUID | None = None
    closed_at: datetime | None = None
    created_by: uuid.UUID | None = None
    created_at: datetime
    updated_at: datetime


# ============================================================ Fase 3 — Payrolls (employee)

PayrollStatus = Literal["pending", "calculated", "approved", "paid", "cancelled"]


class PayrollItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    concept_code: str
    concept_name: str
    concept_type: ConceptType
    category: str | None = None
    quantity: Decimal | None = None
    rate: Decimal | None = None
    base_amount: Decimal | None = None
    percentage: Decimal | None = None
    amount: Decimal
    sort_order: int


class PayrollResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    period_id: uuid.UUID
    employee_id: uuid.UUID
    contract_id: uuid.UUID | None = None
    employee_code: str
    employee_name: str
    department_name: str | None = None
    position_name: str | None = None
    base_salary: Decimal
    worked_days: Decimal
    absence_days: Decimal
    total_earnings: Decimal
    total_deductions: Decimal
    total_benefits: Decimal
    total_employer_contrib: Decimal
    net_amount: Decimal
    status: PayrollStatus
    paid_at: datetime | None = None
    payment_reference: str | None = None
    notes: str | None = None
    created_at: datetime
    updated_at: datetime


class PayrollWithItems(PayrollResponse):
    items: list[PayrollItemResponse] = []


class PayrollListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    employee_id: uuid.UUID
    employee_code: str
    employee_name: str
    department_name: str | None = None
    base_salary: Decimal
    total_earnings: Decimal
    total_deductions: Decimal
    net_amount: Decimal
    status: PayrollStatus


class CalculationResult(BaseModel):
    period_id: uuid.UUID
    employees_processed: int
    total_gross: Decimal
    total_deductions: Decimal
    total_net: Decimal


class PayrollPaymentRequest(BaseModel):
    payment_reference: str | None = None
    create_finance_transaction: bool = True
