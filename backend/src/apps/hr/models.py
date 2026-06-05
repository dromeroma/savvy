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
