"""Schemas Pydantic para RRHH (cargos, empleados, asistencia)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


ContractType = Literal["indefinido", "fijo", "obra_labor", "prestacion", "aprendiz", "otro"]
EmployeeStatus = Literal["active", "on_leave", "suspended", "terminated"]
ShiftKind = Literal["morning", "afternoon", "night", "rotating", "administrative"]
AttendanceStatus = Literal["present", "absent", "late", "justified", "vacation", "sick_leave"]


# ---------------------------------------------------------------- Positions


class PositionBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    name: str = Field(..., min_length=1, max_length=150)
    description: str | None = None
    is_active: bool = True


class PositionCreate(PositionBase):
    pass


class PositionUpdate(BaseModel):
    name: str | None = Field(None, max_length=150)
    description: str | None = None
    is_active: bool | None = None


class PositionResponse(PositionBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


# ---------------------------------------------------------------- Employees


class EmployeeBase(BaseModel):
    code: str = Field(..., min_length=1, max_length=40)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str | None = Field(None, max_length=100)
    document_type: str | None = Field(None, max_length=10)
    document_number: str | None = Field(None, max_length=50)
    birth_date: date | None = None
    gender: str | None = Field(None, max_length=10)
    email: EmailStr | None = None
    phone: str | None = Field(None, max_length=50)
    mobile: str | None = Field(None, max_length=50)
    address: str | None = Field(None, max_length=255)
    position_id: uuid.UUID | None = None
    contract_type: ContractType = "indefinido"
    hire_date: date
    end_date: date | None = None
    base_salary: Decimal = Field(default=Decimal("0"), ge=0)
    default_shift: ShiftKind | None = None
    status: EmployeeStatus = "active"
    user_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None
    notes: str | None = None


class EmployeeCreate(EmployeeBase):
    pass


class EmployeeUpdate(BaseModel):
    first_name: str | None = Field(None, max_length=100)
    last_name: str | None = None
    document_type: str | None = None
    document_number: str | None = None
    birth_date: date | None = None
    gender: str | None = None
    email: EmailStr | None = None
    phone: str | None = None
    mobile: str | None = None
    address: str | None = None
    position_id: uuid.UUID | None = None
    contract_type: ContractType | None = None
    end_date: date | None = None
    base_salary: Decimal | None = Field(None, ge=0)
    default_shift: ShiftKind | None = None
    status: EmployeeStatus | None = None
    user_id: uuid.UUID | None = None
    driver_id: uuid.UUID | None = None
    notes: str | None = None


class EmployeeResponse(EmployeeBase):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    created_at: datetime
    updated_at: datetime


class EmployeeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    code: str
    first_name: str
    last_name: str | None
    document_number: str | None
    position_id: uuid.UUID | None
    position_name: str | None
    contract_type: str
    hire_date: date
    status: str
    base_salary: Decimal
    default_shift: str | None


# ---------------------------------------------------------------- Attendance


class AttendanceCreate(BaseModel):
    """Crear/upsert un registro de asistencia. Si ya existe para
    (empleado, fecha), se actualiza."""

    employee_id: uuid.UUID
    work_date: date
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    status: AttendanceStatus = "present"
    notes: str | None = None


class AttendanceUpdate(BaseModel):
    check_in_at: datetime | None = None
    check_out_at: datetime | None = None
    status: AttendanceStatus | None = None
    notes: str | None = None


class AttendanceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    employee_id: uuid.UUID
    work_date: date
    check_in_at: datetime | None
    check_out_at: datetime | None
    hours_worked: Decimal | None
    status: str
    notes: str | None
    created_at: datetime
    updated_at: datetime


class AttendanceListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    employee_id: uuid.UUID
    employee_code: str
    employee_name: str
    work_date: date
    check_in_at: datetime | None
    check_out_at: datetime | None
    hours_worked: Decimal | None
    status: str
