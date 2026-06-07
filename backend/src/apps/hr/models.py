"""SavvyHR SQLAlchemy models — fase 1: estructura + empleados + contratos + docs."""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


# ---------------------------------------------------------------- Department


class HrDepartment(BaseMixin, OrgMixin, Base):
    """Departamento o unidad organizacional. Jerárquico vía parent_id."""

    __tablename__ = "hr_departments"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_hr_departments_org_code"),
    )

    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_departments.id", ondelete="SET NULL"), nullable=True,
    )
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    cost_center: Mapped[str | None] = mapped_column(String(40), nullable=True)
    manager_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="SET NULL"), nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# ---------------------------------------------------------------- Position


class HrPosition(BaseMixin, OrgMixin, Base):
    """Cargo con escala salarial y vínculo opcional a departamento."""

    __tablename__ = "hr_positions"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_hr_positions_org_code"),
    )

    department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_departments.id", ondelete="SET NULL"), nullable=True,
    )
    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    level: Mapped[int | None] = mapped_column(Integer, nullable=True)
    min_salary: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    max_salary: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    reference_salary: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    currency: Mapped[str] = mapped_column(String(3), default="COP", nullable=False)
    headcount_budget: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# ---------------------------------------------------------------- Employee


class HrEmployee(BaseMixin, OrgMixin, Base):
    """Empleado del talento humano.

    Vínculo opcional con `people.id` para reusar identidad cross-app
    (un mismo person_id puede ser estudiante en edu + empleado en hr).
    """

    __tablename__ = "hr_employees"
    __table_args__ = (
        UniqueConstraint("organization_id", "employee_code", name="uq_hr_employees_org_code"),
        UniqueConstraint("organization_id", "person_id", name="uq_hr_employees_org_person"),
        CheckConstraint(
            "status IN ('active','on_leave','suspended','terminated')",
            name="chk_hr_employees_status",
        ),
        CheckConstraint(
            "employment_type IN ('full_time','part_time','intern','contractor','temporary')",
            name="chk_hr_employees_employment_type",
        ),
        CheckConstraint(
            "work_location IN ('onsite','remote','hybrid')",
            name="chk_hr_employees_work_location",
        ),
    )

    person_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    employee_code: Mapped[str] = mapped_column(String(40), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    marital_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    emergency_contact_relationship: Mapped[str | None] = mapped_column(String(40), nullable=True)

    department_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_departments.id", ondelete="SET NULL"), nullable=True,
    )
    position_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_positions.id", ondelete="SET NULL"), nullable=True,
    )
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="SET NULL"), nullable=True,
    )

    hire_date: Mapped[date] = mapped_column(Date, nullable=False)
    termination_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    termination_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    employment_type: Mapped[str] = mapped_column(String(20), default="full_time", nullable=False)
    work_location: Mapped[str] = mapped_column(String(20), default="onsite", nullable=False)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# ---------------------------------------------------------------- Contract


class HrContract(BaseMixin, OrgMixin, Base):
    """Contrato laboral del empleado. Un empleado puede tener varios
    contratos en el tiempo; el activo se determina por status + fechas."""

    __tablename__ = "hr_contracts"
    __table_args__ = (
        UniqueConstraint("organization_id", "contract_number", name="uq_hr_contracts_org_number"),
        CheckConstraint(
            "contract_type IN ('indefinido','fijo','obra_labor','prestacion','aprendiz','practicante','otro')",
            name="chk_hr_contracts_type",
        ),
        CheckConstraint(
            "payment_frequency IN ('monthly','biweekly','weekly')",
            name="chk_hr_contracts_frequency",
        ),
        CheckConstraint(
            "status IN ('draft','active','suspended','terminated','expired')",
            name="chk_hr_contracts_status",
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False,
    )
    contract_number: Mapped[str] = mapped_column(String(40), nullable=False)
    contract_type: Mapped[str] = mapped_column(String(30), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    trial_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    renewal_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    base_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="COP", nullable=False)
    payment_frequency: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False)
    weekly_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("48"), nullable=False)

    transport_allowance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    food_allowance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    connectivity_allowance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    other_allowance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)

    risk_class: Mapped[str | None] = mapped_column(String(10), nullable=True)
    eps_provider: Mapped[str | None] = mapped_column(String(150), nullable=True)
    pension_provider: Mapped[str | None] = mapped_column(String(150), nullable=True)
    severance_provider: Mapped[str | None] = mapped_column(String(150), nullable=True)
    compensation_fund: Mapped[str | None] = mapped_column(String(150), nullable=True)

    bank_name: Mapped[str | None] = mapped_column(String(80), nullable=True)
    bank_account_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    bank_account_number: Mapped[str | None] = mapped_column(String(40), nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    terminated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    termination_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# ---------------------------------------------------------------- Document


class HrEmployeeDocument(BaseMixin, OrgMixin, Base):
    """Documento del empleado: HV, contrato, afiliaciones, exámenes."""

    __tablename__ = "hr_employee_documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('valid','expired','revoked','pending_review')",
            name="chk_hr_doc_status",
        ),
        CheckConstraint(
            "document_type IN ("
            "'resume','contract','id_copy','tax_id',"
            "'eps_affiliation','pension_affiliation','severance_affiliation',"
            "'arl_affiliation','compensation_fund_affiliation',"
            "'medical_exam','background_check','study_certificate','work_certificate',"
            "'training_certificate','disciplinary_record','other')",
            name="chk_hr_doc_type",
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False,
    )
    document_type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    issue_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    issuer: Mapped[str | None] = mapped_column(String(150), nullable=True)
    reference_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="valid", nullable=False)
    uploaded_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# ============================================================ Fase 2 — Shifts


class HrShift(BaseMixin, OrgMixin, Base):
    """Turno configurable (mañana, tarde, noche, rotativo, flexible)."""

    __tablename__ = "hr_shifts"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_hr_shifts_org_code"),
        CheckConstraint(
            "shift_type IN ('morning','afternoon','night','rotating','flexible','administrative')",
            name="chk_hr_shifts_type",
        ),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    shift_type: Mapped[str] = mapped_column(String(20), default="morning", nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    break_minutes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    days_of_week: Mapped[list[int]] = mapped_column(
        JSONB, default=lambda: [1, 2, 3, 4, 5], nullable=False,
    )
    weekly_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# ============================================================ Fase 2 — Attendance


class HrAttendance(BaseMixin, OrgMixin, Base):
    """Registro de asistencia diario por empleado."""

    __tablename__ = "hr_attendance"
    __table_args__ = (
        UniqueConstraint("employee_id", "work_date", name="uq_hr_att_emp_date"),
        CheckConstraint(
            "status IN ('present','absent','late','early_leave','justified','vacation','sick_leave','permit','holiday')",
            name="chk_hr_att_status",
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False,
    )
    shift_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_shifts.id", ondelete="SET NULL"), nullable=True,
    )
    work_date: Mapped[date] = mapped_column(Date, nullable=False)
    check_in_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    check_out_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    planned_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    worked_hours: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    overtime_day_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    overtime_night_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    overtime_holiday_hours: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("0"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="present", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# ============================================================ Fase 2 — Vacation balances


class HrVacationBalance(BaseMixin, OrgMixin, Base):
    """Saldo anual de vacaciones por empleado.

    days_available = days_accrued - days_taken - days_pending - days_compensated
    """

    __tablename__ = "hr_vacation_balances"
    __table_args__ = (
        UniqueConstraint("employee_id", "period_year", name="uq_hr_vac_bal_emp_year"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False,
    )
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    days_accrued: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"), nullable=False)
    days_taken: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"), nullable=False)
    days_pending: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"), nullable=False)
    days_compensated: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"), nullable=False)
    last_accrual_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ============================================================ Fase 2 — Vacation requests


class HrVacationRequest(BaseMixin, OrgMixin, Base):
    """Solicitud de vacaciones con flujo de aprobación."""

    __tablename__ = "hr_vacation_requests"
    __table_args__ = (
        UniqueConstraint("organization_id", "request_number", name="uq_hr_vac_req_org_number"),
        CheckConstraint(
            "request_type IN ('paid','compensation','unpaid')",
            name="chk_hr_vac_req_type",
        ),
        CheckConstraint(
            "status IN ('pending','approved','rejected','cancelled','completed')",
            name="chk_hr_vac_req_status",
        ),
        CheckConstraint("end_date >= start_date", name="chk_hr_vac_req_dates"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False,
    )
    request_number: Mapped[str] = mapped_column(String(40), nullable=False)
    request_type: Mapped[str] = mapped_column(String(20), default="paid", nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_count: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    request_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    compensation_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    rejected_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    rejected_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# ============================================================ Fase 2 — Leaves


class HrLeave(BaseMixin, OrgMixin, Base):
    """Incapacidad, licencia o permiso. Distinta de vacaciones."""

    __tablename__ = "hr_leaves"
    __table_args__ = (
        UniqueConstraint("organization_id", "leave_number", name="uq_hr_leaves_org_number"),
        CheckConstraint(
            "leave_type IN ('medical','maternity','paternity','bereavement','unpaid','paid_other','study','remunerated_permit')",
            name="chk_hr_leaves_type",
        ),
        CheckConstraint(
            "status IN ('active','completed','cancelled')",
            name="chk_hr_leaves_status",
        ),
        CheckConstraint("end_date >= start_date", name="chk_hr_leaves_dates"),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False,
    )
    leave_number: Mapped[str] = mapped_column(String(40), nullable=False)
    leave_type: Mapped[str] = mapped_column(String(30), nullable=False)
    subtype: Mapped[str | None] = mapped_column(String(40), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    days_count: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    is_paid: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    paid_percentage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    amount_paid: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    supporting_doc_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    supporting_doc_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    supporting_doc_issuer: Mapped[str | None] = mapped_column(String(150), nullable=True)
    diagnosis_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# ============================================================ Fase 3 — Payroll concepts


class HrPayrollConcept(BaseMixin, OrgMixin, Base):
    """Catálogo configurable de conceptos de nómina (devengados, deducciones,
    prestaciones, aportes patronales). Soporta multi-país."""

    __tablename__ = "hr_payroll_concepts"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_hr_concepts_org_code"),
        CheckConstraint(
            "concept_type IN ('earning','deduction','benefit','employer_contribution','informative')",
            name="chk_hr_concept_type",
        ),
        CheckConstraint(
            "calculation_method IN ('fixed','percentage','formula','quantity_rate')",
            name="chk_hr_concept_method",
        ),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    concept_type: Mapped[str] = mapped_column(String(30), nullable=False)
    category: Mapped[str] = mapped_column(String(40), nullable=False)
    calculation_method: Mapped[str] = mapped_column(String(20), default="fixed", nullable=False)
    formula: Mapped[str | None] = mapped_column(Text, nullable=True)
    percentage_value: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    fixed_value: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    base_concept_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    country_code: Mapped[str | None] = mapped_column(String(3), nullable=True)
    is_taxable: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)


# ============================================================ Fase 3 — Payroll period


class HrPayrollPeriod(BaseMixin, OrgMixin, Base):
    """Período de nómina (mensual, quincenal, semanal)."""

    __tablename__ = "hr_payroll_periods"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_hr_periods_org_code"),
        CheckConstraint(
            "period_type IN ('monthly','biweekly','weekly')",
            name="chk_hr_period_type",
        ),
        CheckConstraint(
            "status IN ('draft','calculating','calculated','approved','paid','closed','cancelled')",
            name="chk_hr_period_status",
        ),
        CheckConstraint("end_date >= start_date", name="chk_hr_period_dates"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    period_type: Mapped[str] = mapped_column(String(20), default="monthly", nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    total_gross: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    total_net: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    employee_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    calculated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    paid_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# ============================================================ Fase 3 — Payroll (liquidación por empleado)


class HrPayroll(BaseMixin, OrgMixin, Base):
    """Liquidación de un empleado en un período concreto."""

    __tablename__ = "hr_payrolls"
    __table_args__ = (
        UniqueConstraint("period_id", "employee_id", name="uq_hr_payroll_period_emp"),
        CheckConstraint(
            "status IN ('pending','calculated','approved','paid','cancelled')",
            name="chk_hr_payroll_status",
        ),
    )

    period_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_payroll_periods.id", ondelete="CASCADE"), nullable=False,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False,
    )
    contract_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_contracts.id", ondelete="SET NULL"), nullable=True,
    )
    employee_code: Mapped[str] = mapped_column(String(40), nullable=False)
    employee_name: Mapped[str] = mapped_column(String(255), nullable=False)
    department_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    position_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    base_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    worked_days: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("30"), nullable=False)
    absence_days: Mapped[Decimal] = mapped_column(Numeric(6, 2), default=Decimal("0"), nullable=False)
    total_earnings: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    total_benefits: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    total_employer_contrib: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), default=Decimal("0"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="calculated", nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    payment_reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    finance_transaction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    pay_transaction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ============================================================ Fase 3 — Payroll items (líneas)


class HrPayrollItem(Base):
    """Línea detalle de una liquidación: concepto × monto."""

    __tablename__ = "hr_payroll_items"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payroll_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_payrolls.id", ondelete="CASCADE"), nullable=False,
    )
    concept_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_payroll_concepts.id", ondelete="SET NULL"), nullable=True,
    )
    concept_code: Mapped[str] = mapped_column(String(40), nullable=False)
    concept_name: Mapped[str] = mapped_column(String(150), nullable=False)
    concept_type: Mapped[str] = mapped_column(String(30), nullable=False)
    category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    rate: Mapped[Decimal | None] = mapped_column(Numeric(14, 4), nullable=True)
    base_amount: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    percentage: Mapped[Decimal | None] = mapped_column(Numeric(8, 4), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(15, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


# ============================================================ Fase 4 — Evaluation cycle


class HrEvaluationCycle(BaseMixin, OrgMixin, Base):
    """Ciclo de evaluación: plantilla de competencias + escala + período."""

    __tablename__ = "hr_evaluation_cycles"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_hr_eval_cycle_code"),
        CheckConstraint(
            "status IN ('draft','open','closed','cancelled')",
            name="chk_hr_eval_cycle_status",
        ),
        CheckConstraint("end_date >= start_date", name="chk_hr_eval_cycle_dates"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    period_label: Mapped[str | None] = mapped_column(String(40), nullable=True)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    enable_self: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_supervisor: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    enable_360: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    scale_min: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("1"), nullable=False)
    scale_max: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=Decimal("5"), nullable=False)
    # competencies: [{code, name, weight, description}]
    competencies: Mapped[list[dict]] = mapped_column(JSONB, default=list, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# ============================================================ Fase 4 — Evaluation


class HrEvaluation(BaseMixin, OrgMixin, Base):
    """Evaluación de un empleado en un ciclo concreto."""

    __tablename__ = "hr_evaluations"
    __table_args__ = (
        UniqueConstraint("cycle_id", "employee_id", name="uq_hr_eval_cycle_emp"),
        CheckConstraint(
            "status IN ('pending','in_progress','completed','cancelled')",
            name="chk_hr_eval_status",
        ),
    )

    cycle_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_evaluation_cycles.id", ondelete="CASCADE"), nullable=False,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False,
    )
    supervisor_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="SET NULL"), nullable=True,
    )
    self_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    self_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    supervisor_completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supervisor_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    peer_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    peer_avg: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    overall_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    improvement_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# ============================================================ Fase 4 — Evaluation response


class HrEvaluationResponse(Base):
    """Respuesta individual a una evaluación: auto, jefe, peer, subordinate."""

    __tablename__ = "hr_evaluation_responses"
    __table_args__ = (
        CheckConstraint(
            "evaluator_type IN ('self','supervisor','peer','subordinate')",
            name="chk_hr_eval_resp_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_evaluations.id", ondelete="CASCADE"), nullable=False,
    )
    evaluator_type: Mapped[str] = mapped_column(String(20), nullable=False)
    evaluator_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    evaluator_employee_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="SET NULL"), nullable=True,
    )
    # scores: {competency_code: score, ...}
    scores: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    overall_score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


# ============================================================ Fase 4 — Training course


class HrTrainingCourse(BaseMixin, OrgMixin, Base):
    """Curso del catálogo de capacitaciones."""

    __tablename__ = "hr_training_courses"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_hr_training_courses_code"),
        CheckConstraint(
            "delivery_mode IN ('in_person','virtual_live','virtual_async','hybrid','external')",
            name="chk_hr_training_mode",
        ),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(40), default="general", nullable=False)
    duration_hours: Mapped[Decimal | None] = mapped_column(Numeric(6, 2), nullable=True)
    delivery_mode: Mapped[str] = mapped_column(String(20), default="in_person", nullable=False)
    is_mandatory: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    provider: Mapped[str | None] = mapped_column(String(150), nullable=True)
    cost_per_seat: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    certificate_template_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


# ============================================================ Fase 4 — Training enrollment


class HrTrainingEnrollment(BaseMixin, OrgMixin, Base):
    """Inscripción de empleado en un curso."""

    __tablename__ = "hr_training_enrollments"
    __table_args__ = (
        CheckConstraint(
            "completion_status IN ('enrolled','in_progress','completed','failed','cancelled')",
            name="chk_hr_training_enr_status",
        ),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_training_courses.id", ondelete="CASCADE"), nullable=False,
    )
    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False,
    )
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completion_status: Mapped[str] = mapped_column(String(20), default="enrolled", nullable=False)
    score: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    attendance_pct: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    certificate_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    certificate_number: Mapped[str | None] = mapped_column(String(80), nullable=True)
    cost: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    enrolled_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# ============================================================ Fase 5 — Liquidación + Settings


class HrSettings(BaseMixin, OrgMixin, Base):
    """Configuración HR por organización (1:1)."""

    __tablename__ = "hr_settings"
    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_hr_settings_org"),
        CheckConstraint(
            "default_liquidation_template IN ('formal','moderna','compacta')",
            name="chk_hr_settings_template",
        ),
    )

    default_liquidation_template: Mapped[str] = mapped_column(
        String(20), default="formal", nullable=False,
    )
    liquidation_notes_default: Mapped[str | None] = mapped_column(Text, nullable=True)
    admin_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    admin_title: Mapped[str | None] = mapped_column(String(150), nullable=True)
    signature_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    logo_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    brand_color: Mapped[str | None] = mapped_column(String(20), nullable=True)


class HrLiquidation(BaseMixin, OrgMixin, Base):
    """Liquidación (settlement) al terminar el contrato laboral."""

    __tablename__ = "hr_liquidations"
    __table_args__ = (
        UniqueConstraint("organization_id", "liquidation_number", name="uq_hr_liq_org_number"),
        CheckConstraint(
            "termination_reason IN ('voluntary','mutual','with_cause','without_cause',"
            "'end_of_contract','retirement','death','other')",
            name="chk_hr_liq_reason",
        ),
        CheckConstraint(
            "status IN ('draft','finalized','paid','cancelled')",
            name="chk_hr_liq_status",
        ),
    )

    employee_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_employees.id", ondelete="CASCADE"), nullable=False,
    )
    contract_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("hr_contracts.id", ondelete="SET NULL"), nullable=True,
    )
    liquidation_number: Mapped[str] = mapped_column(String(40), nullable=False)
    termination_date: Mapped[date] = mapped_column(Date, nullable=False)
    termination_reason: Mapped[str] = mapped_column(String(30), nullable=False)
    last_worked_date: Mapped[date] = mapped_column(Date, nullable=False)
    contract_start_date: Mapped[date] = mapped_column(Date, nullable=False)

    base_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    average_salary: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    days_worked_total: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    total_earnings: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    total_deductions: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    net_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), default="COP", nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="draft", nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    finalized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_template: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    finalized_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


class HrLiquidationItem(BaseMixin, OrgMixin, Base):
    """Línea individual de la liquidación (concepto + monto)."""

    __tablename__ = "hr_liquidation_items"
    __table_args__ = (
        CheckConstraint(
            "kind IN ('earning','deduction')",
            name="chk_hr_liq_item_kind",
        ),
    )

    liquidation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("hr_liquidations.id", ondelete="CASCADE"), nullable=False,
    )
    concept_code: Mapped[str] = mapped_column(String(60), nullable=False)
    concept_name: Mapped[str] = mapped_column(String(200), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("1"), nullable=False)
    base_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    rate: Mapped[Decimal | None] = mapped_column(Numeric(10, 4), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    is_manual: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
