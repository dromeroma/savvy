"""Lógica de RRHH: cargos, empleados, asistencia."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.hr.schemas import (
    AttendanceCreate,
    AttendanceListItem,
    AttendanceUpdate,
    EmployeeCreate,
    EmployeeListItem,
    EmployeeUpdate,
    PositionCreate,
    PositionUpdate,
)
from src.apps.memorial.models import (
    MemorialAttendance,
    MemorialEmployee,
    MemorialPosition,
)
from src.core.exceptions import ConflictError, NotFoundError


# ---------------------------------------------------------------- Positions


class PositionsService:

    @staticmethod
    async def list_(db, org_id, active_only: bool = False):
        stmt = (
            select(MemorialPosition)
            .where(MemorialPosition.organization_id == org_id)
            .order_by(MemorialPosition.code)
        )
        if active_only:
            stmt = stmt.where(MemorialPosition.is_active.is_(True))
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db, org_id, pid):
        p = await db.scalar(
            select(MemorialPosition).where(
                MemorialPosition.id == pid,
                MemorialPosition.organization_id == org_id,
            )
        )
        if p is None:
            raise NotFoundError("Cargo no encontrado.")
        return p

    @staticmethod
    async def create(db, org_id, data: PositionCreate):
        existing = await db.scalar(
            select(MemorialPosition).where(
                MemorialPosition.organization_id == org_id,
                MemorialPosition.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un cargo con código '{data.code}'.")
        p = MemorialPosition(organization_id=org_id, **data.model_dump())
        db.add(p)
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def update(db, org_id, pid, data: PositionUpdate):
        p = await PositionsService.get(db, org_id, pid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(p, k, v)
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def delete(db, org_id, pid):
        in_use = await db.scalar(
            select(func.count(MemorialEmployee.id)).where(
                MemorialEmployee.position_id == pid,
            )
        )
        if int(in_use or 0) > 0:
            raise ConflictError(
                "Cargo asignado a empleados — desactívalo en vez de eliminarlo.",
            )
        p = await PositionsService.get(db, org_id, pid)
        await db.delete(p)
        await db.flush()


# ---------------------------------------------------------------- Employees


class EmployeesService:

    @staticmethod
    async def list_(
        db: AsyncSession,
        org_id: uuid.UUID,
        status: str | None = None,
        position_id: uuid.UUID | None = None,
        search: str | None = None,
    ) -> list[EmployeeListItem]:
        stmt = (
            select(
                MemorialEmployee,
                MemorialPosition.name.label("position_name"),
            )
            .outerjoin(MemorialPosition, MemorialPosition.id == MemorialEmployee.position_id)
            .where(MemorialEmployee.organization_id == org_id)
            .order_by(MemorialEmployee.status, MemorialEmployee.code)
        )
        if status:
            stmt = stmt.where(MemorialEmployee.status == status)
        if position_id:
            stmt = stmt.where(MemorialEmployee.position_id == position_id)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(MemorialEmployee.code).like(like),
                    func.lower(MemorialEmployee.first_name).like(like),
                    func.lower(func.coalesce(MemorialEmployee.last_name, "")).like(like),
                    func.lower(func.coalesce(MemorialEmployee.document_number, "")).like(like),
                )
            )
        rows = await db.execute(stmt)
        out: list[EmployeeListItem] = []
        for e, position_name in rows.all():
            out.append(EmployeeListItem(
                id=e.id, code=e.code,
                first_name=e.first_name, last_name=e.last_name,
                document_number=e.document_number,
                position_id=e.position_id, position_name=position_name,
                contract_type=e.contract_type, hire_date=e.hire_date,
                status=e.status, base_salary=e.base_salary,
                default_shift=e.default_shift,
            ))
        return out

    @staticmethod
    async def get(db, org_id, eid):
        e = await db.scalar(
            select(MemorialEmployee).where(
                MemorialEmployee.id == eid,
                MemorialEmployee.organization_id == org_id,
            )
        )
        if e is None:
            raise NotFoundError("Empleado no encontrado.")
        return e

    @staticmethod
    async def create(db, org_id, data: EmployeeCreate):
        existing = await db.scalar(
            select(MemorialEmployee).where(
                MemorialEmployee.organization_id == org_id,
                MemorialEmployee.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un empleado con código '{data.code}'.")
        e = MemorialEmployee(organization_id=org_id, **data.model_dump())
        db.add(e)
        await db.flush()
        await db.refresh(e)
        return e

    @staticmethod
    async def update(db, org_id, eid, data: EmployeeUpdate):
        e = await EmployeesService.get(db, org_id, eid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(e, k, v)
        await db.flush()
        await db.refresh(e)
        return e

    @staticmethod
    async def delete(db, org_id, eid):
        in_use = await db.scalar(
            select(func.count(MemorialAttendance.id)).where(
                MemorialAttendance.employee_id == eid,
            )
        )
        if int(in_use or 0) > 0:
            raise ConflictError(
                "Empleado con registros de asistencia — cámbialo a 'terminated' en vez de eliminarlo.",
            )
        e = await EmployeesService.get(db, org_id, eid)
        await db.delete(e)
        await db.flush()


# ---------------------------------------------------------------- Attendance


class AttendanceService:

    @staticmethod
    def _compute_hours(check_in, check_out) -> Decimal | None:
        if check_in is None or check_out is None:
            return None
        delta = check_out - check_in
        hours = Decimal(delta.total_seconds()) / Decimal(3600)
        return hours.quantize(Decimal("0.01"))

    @staticmethod
    async def list_(
        db: AsyncSession,
        org_id: uuid.UUID,
        employee_id: uuid.UUID | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        status: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[AttendanceListItem]:
        stmt = (
            select(
                MemorialAttendance,
                MemorialEmployee.code.label("e_code"),
                MemorialEmployee.first_name,
                MemorialEmployee.last_name,
            )
            .join(MemorialEmployee, MemorialEmployee.id == MemorialAttendance.employee_id)
            .where(MemorialAttendance.organization_id == org_id)
            .order_by(MemorialAttendance.work_date.desc(), MemorialAttendance.created_at.desc())
            .limit(limit).offset(offset)
        )
        if employee_id:
            stmt = stmt.where(MemorialAttendance.employee_id == employee_id)
        if status:
            stmt = stmt.where(MemorialAttendance.status == status)
        if date_from:
            stmt = stmt.where(MemorialAttendance.work_date >= date_from)
        if date_to:
            stmt = stmt.where(MemorialAttendance.work_date <= date_to)
        rows = await db.execute(stmt)
        out: list[AttendanceListItem] = []
        for a, e_code, first, last in rows.all():
            name = f"{first} {last or ''}".strip()
            out.append(AttendanceListItem(
                id=a.id, employee_id=a.employee_id,
                employee_code=e_code, employee_name=name,
                work_date=a.work_date,
                check_in_at=a.check_in_at, check_out_at=a.check_out_at,
                hours_worked=a.hours_worked, status=a.status,
            ))
        return out

    @staticmethod
    async def upsert(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: AttendanceCreate,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialAttendance:
        # Validar empleado
        emp = await db.scalar(
            select(MemorialEmployee).where(
                MemorialEmployee.id == data.employee_id,
                MemorialEmployee.organization_id == org_id,
            )
        )
        if emp is None:
            raise NotFoundError("Empleado no encontrado.")

        existing = await db.scalar(
            select(MemorialAttendance).where(
                MemorialAttendance.employee_id == data.employee_id,
                MemorialAttendance.work_date == data.work_date,
            )
        )
        hours = AttendanceService._compute_hours(data.check_in_at, data.check_out_at)
        if existing is not None:
            existing.check_in_at = data.check_in_at
            existing.check_out_at = data.check_out_at
            existing.status = data.status
            existing.notes = data.notes
            existing.hours_worked = hours
            await db.flush()
            return existing
        a = MemorialAttendance(
            organization_id=org_id,
            employee_id=data.employee_id,
            work_date=data.work_date,
            check_in_at=data.check_in_at,
            check_out_at=data.check_out_at,
            hours_worked=hours,
            status=data.status,
            notes=data.notes,
            recorded_by=actor_user_id,
        )
        db.add(a)
        await db.flush()
        return a

    @staticmethod
    async def update(
        db: AsyncSession,
        org_id: uuid.UUID,
        att_id: uuid.UUID,
        data: AttendanceUpdate,
    ) -> MemorialAttendance:
        a = await db.scalar(
            select(MemorialAttendance).where(
                MemorialAttendance.id == att_id,
                MemorialAttendance.organization_id == org_id,
            )
        )
        if a is None:
            raise NotFoundError("Registro de asistencia no encontrado.")
        changes = data.model_dump(exclude_unset=True)
        for k, v in changes.items():
            setattr(a, k, v)
        # recompute hours
        a.hours_worked = AttendanceService._compute_hours(a.check_in_at, a.check_out_at)
        await db.flush()
        return a

    @staticmethod
    async def delete(db, org_id, att_id):
        a = await db.scalar(
            select(MemorialAttendance).where(
                MemorialAttendance.id == att_id,
                MemorialAttendance.organization_id == org_id,
            )
        )
        if a is None:
            raise NotFoundError("Registro no encontrado.")
        await db.delete(a)
        await db.flush()
