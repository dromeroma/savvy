"""SavvyHR services — fase 2: shifts, attendance, vacations, leaves."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hr.models import (
    HrAttendance,
    HrEmployee,
    HrLeave,
    HrShift,
    HrVacationBalance,
    HrVacationRequest,
)
from src.apps.hr.schemas import (
    AttendanceCreate,
    AttendanceUpdate,
    LeaveCreate,
    LeaveUpdate,
    ShiftCreate,
    ShiftUpdate,
    VacationBalanceAdjust,
    VacationRequestCreate,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


def _now() -> datetime:
    return datetime.now(UTC)


# ============================================================ Shifts


class ShiftsService:

    @staticmethod
    async def list_(db: AsyncSession, org_id: uuid.UUID, active_only: bool = False):
        stmt = select(HrShift).where(HrShift.organization_id == org_id).order_by(HrShift.code)
        if active_only:
            stmt = stmt.where(HrShift.is_active.is_(True))
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, sid: uuid.UUID) -> HrShift:
        s = await db.scalar(
            select(HrShift).where(HrShift.id == sid, HrShift.organization_id == org_id)
        )
        if s is None:
            raise NotFoundError("Turno no encontrado.")
        return s

    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, data: ShiftCreate) -> HrShift:
        existing = await db.scalar(
            select(HrShift).where(
                HrShift.organization_id == org_id, HrShift.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un turno con código '{data.code}'.")
        s = HrShift(organization_id=org_id, **data.model_dump())
        db.add(s)
        await db.flush()
        await db.refresh(s)
        return s

    @staticmethod
    async def update(db: AsyncSession, org_id: uuid.UUID, sid: uuid.UUID, data: ShiftUpdate) -> HrShift:
        s = await ShiftsService.get(db, org_id, sid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(s, k, v)
        await db.flush()
        await db.refresh(s)
        return s

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, sid: uuid.UUID) -> None:
        s = await ShiftsService.get(db, org_id, sid)
        await db.delete(s)
        await db.flush()


# ============================================================ Attendance


def _compute_worked_hours(check_in: datetime | None, check_out: datetime | None) -> Decimal | None:
    if check_in is None or check_out is None:
        return None
    delta = check_out - check_in
    seconds = delta.total_seconds()
    if seconds <= 0:
        return Decimal("0")
    hours = Decimal(str(seconds / 3600))
    return hours.quantize(Decimal("0.01"))


class AttendanceService:

    @staticmethod
    async def list_(
        db: AsyncSession,
        org_id: uuid.UUID,
        *,
        employee_id: uuid.UUID | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
        status: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ):
        stmt = (
            select(
                HrAttendance.id,
                HrAttendance.employee_id,
                HrEmployee.employee_code,
                (HrEmployee.first_name + " " + func.coalesce(HrEmployee.last_name, "")).label("employee_name"),
                HrAttendance.work_date,
                HrAttendance.check_in_at,
                HrAttendance.check_out_at,
                HrAttendance.worked_hours,
                (HrAttendance.overtime_day_hours + HrAttendance.overtime_night_hours + HrAttendance.overtime_holiday_hours).label("overtime_total"),
                HrAttendance.status,
            )
            .where(HrAttendance.organization_id == org_id)
            .join(HrEmployee, HrEmployee.id == HrAttendance.employee_id)
            .order_by(HrAttendance.work_date.desc(), HrEmployee.employee_code)
            .limit(limit).offset(offset)
        )
        if employee_id:
            stmt = stmt.where(HrAttendance.employee_id == employee_id)
        if date_from:
            stmt = stmt.where(HrAttendance.work_date >= date_from)
        if date_to:
            stmt = stmt.where(HrAttendance.work_date <= date_to)
        if status:
            stmt = stmt.where(HrAttendance.status == status)
        rows = await db.execute(stmt)
        return [dict(r._mapping) for r in rows.all()]

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, aid: uuid.UUID) -> HrAttendance:
        a = await db.scalar(
            select(HrAttendance).where(HrAttendance.id == aid, HrAttendance.organization_id == org_id)
        )
        if a is None:
            raise NotFoundError("Registro de asistencia no encontrado.")
        return a

    @staticmethod
    async def upsert(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: AttendanceCreate,
        recorded_by: uuid.UUID | None,
    ) -> HrAttendance:
        emp = await db.scalar(
            select(HrEmployee).where(
                HrEmployee.id == data.employee_id, HrEmployee.organization_id == org_id,
            )
        )
        if emp is None:
            raise NotFoundError("Empleado no encontrado.")

        payload = data.model_dump()
        if payload.get("worked_hours") is None:
            payload["worked_hours"] = _compute_worked_hours(
                payload.get("check_in_at"), payload.get("check_out_at"),
            )

        existing = await db.scalar(
            select(HrAttendance).where(
                HrAttendance.organization_id == org_id,
                HrAttendance.employee_id == data.employee_id,
                HrAttendance.work_date == data.work_date,
            )
        )
        if existing is not None:
            for k, v in payload.items():
                setattr(existing, k, v)
            await db.flush()
            await db.refresh(existing)
            return existing

        a = HrAttendance(
            organization_id=org_id,
            recorded_by=recorded_by,
            **payload,
        )
        db.add(a)
        await db.flush()
        await db.refresh(a)
        return a

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, aid: uuid.UUID, data: AttendanceUpdate,
    ) -> HrAttendance:
        a = await AttendanceService.get(db, org_id, aid)
        payload = data.model_dump(exclude_unset=True)
        for k, v in payload.items():
            setattr(a, k, v)
        if "check_in_at" in payload or "check_out_at" in payload:
            if a.worked_hours is None or "worked_hours" not in payload:
                a.worked_hours = _compute_worked_hours(a.check_in_at, a.check_out_at)
        await db.flush()
        await db.refresh(a)
        return a

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, aid: uuid.UUID) -> None:
        a = await AttendanceService.get(db, org_id, aid)
        await db.delete(a)
        await db.flush()


# ============================================================ Vacation balances


async def _next_request_number(db: AsyncSession, org_id: uuid.UUID) -> str:
    last = await db.scalar(
        select(func.count(HrVacationRequest.id)).where(
            HrVacationRequest.organization_id == org_id,
        )
    )
    return f"VAC-{(last or 0) + 1:04d}"


async def _next_leave_number(db: AsyncSession, org_id: uuid.UUID) -> str:
    last = await db.scalar(
        select(func.count(HrLeave.id)).where(HrLeave.organization_id == org_id)
    )
    return f"INC-{(last or 0) + 1:04d}"


class VacationBalancesService:

    @staticmethod
    async def list_for_employee(
        db: AsyncSession, org_id: uuid.UUID, employee_id: uuid.UUID,
    ) -> list[HrVacationBalance]:
        rows = await db.execute(
            select(HrVacationBalance)
            .where(
                HrVacationBalance.organization_id == org_id,
                HrVacationBalance.employee_id == employee_id,
            )
            .order_by(HrVacationBalance.period_year.desc())
        )
        return list(rows.scalars().all())

    @staticmethod
    async def list_org(
        db: AsyncSession, org_id: uuid.UUID, period_year: int | None = None,
    ) -> list[HrVacationBalance]:
        stmt = (
            select(HrVacationBalance)
            .where(HrVacationBalance.organization_id == org_id)
            .order_by(HrVacationBalance.period_year.desc())
        )
        if period_year is not None:
            stmt = stmt.where(HrVacationBalance.period_year == period_year)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def _get_or_create(
        db: AsyncSession, org_id: uuid.UUID, employee_id: uuid.UUID, period_year: int,
    ) -> HrVacationBalance:
        bal = await db.scalar(
            select(HrVacationBalance).where(
                HrVacationBalance.organization_id == org_id,
                HrVacationBalance.employee_id == employee_id,
                HrVacationBalance.period_year == period_year,
            )
        )
        if bal is None:
            bal = HrVacationBalance(
                organization_id=org_id, employee_id=employee_id, period_year=period_year,
            )
            db.add(bal)
            await db.flush()
        return bal

    @staticmethod
    async def adjust(
        db: AsyncSession, org_id: uuid.UUID, employee_id: uuid.UUID, data: VacationBalanceAdjust,
    ) -> HrVacationBalance:
        emp = await db.scalar(
            select(HrEmployee).where(
                HrEmployee.id == employee_id, HrEmployee.organization_id == org_id,
            )
        )
        if emp is None:
            raise NotFoundError("Empleado no encontrado.")
        bal = await VacationBalancesService._get_or_create(db, org_id, employee_id, data.period_year)
        if data.days_accrued is not None:
            bal.days_accrued = data.days_accrued
        if data.days_taken is not None:
            bal.days_taken = data.days_taken
        if data.days_compensated is not None:
            bal.days_compensated = data.days_compensated
        if data.notes is not None:
            bal.notes = data.notes
        await db.flush()
        await db.refresh(bal)
        return bal

    @staticmethod
    async def accrue_monthly(
        db: AsyncSession,
        org_id: uuid.UUID,
        *,
        as_of: date | None = None,
        days_per_month: Decimal = Decimal("1.25"),
    ) -> int:
        """Suma `days_per_month` al balance del año actual para cada empleado activo.

        Default 1.25 días/mes (Colombia → 15 días anuales).
        Idempotente por mes: si `last_accrual_at` ya está en este mes, no acumula.
        """
        target = as_of or date.today()
        period_year = target.year
        month_start = target.replace(day=1)

        rows = await db.execute(
            select(HrEmployee).where(
                HrEmployee.organization_id == org_id,
                HrEmployee.status == "active",
            )
        )
        accrued = 0
        for emp in rows.scalars().all():
            bal = await VacationBalancesService._get_or_create(db, org_id, emp.id, period_year)
            if bal.last_accrual_at and bal.last_accrual_at.date() >= month_start:
                continue
            bal.days_accrued = Decimal(bal.days_accrued or 0) + days_per_month
            bal.last_accrual_at = datetime.combine(target, datetime.min.time(), tzinfo=UTC)
            accrued += 1
        await db.flush()
        return accrued


# ============================================================ Vacation requests


class VacationRequestsService:

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID,
        *, employee_id: uuid.UUID | None = None, status: str | None = None,
    ) -> list[HrVacationRequest]:
        stmt = (
            select(HrVacationRequest)
            .where(HrVacationRequest.organization_id == org_id)
            .order_by(HrVacationRequest.requested_at.desc())
        )
        if employee_id:
            stmt = stmt.where(HrVacationRequest.employee_id == employee_id)
        if status:
            stmt = stmt.where(HrVacationRequest.status == status)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID) -> HrVacationRequest:
        r = await db.scalar(
            select(HrVacationRequest).where(
                HrVacationRequest.id == rid, HrVacationRequest.organization_id == org_id,
            )
        )
        if r is None:
            raise NotFoundError("Solicitud de vacaciones no encontrada.")
        return r

    @staticmethod
    async def create(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: VacationRequestCreate,
        created_by: uuid.UUID | None,
    ) -> HrVacationRequest:
        emp = await db.scalar(
            select(HrEmployee).where(
                HrEmployee.id == data.employee_id, HrEmployee.organization_id == org_id,
            )
        )
        if emp is None:
            raise NotFoundError("Empleado no encontrado.")
        number = await _next_request_number(db, org_id)
        r = HrVacationRequest(
            organization_id=org_id,
            request_number=number,
            status="pending",
            created_by=created_by,
            **data.model_dump(),
        )
        db.add(r)
        await db.flush()

        # Reservar saldo en days_pending del año actual
        period = data.start_date.year
        bal = await VacationBalancesService._get_or_create(db, org_id, data.employee_id, period)
        if data.request_type in ("paid", "compensation"):
            bal.days_pending = Decimal(bal.days_pending or 0) + Decimal(data.days_count)

        await db.flush()
        await db.refresh(r)
        return r

    @staticmethod
    async def approve(
        db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID, notes: str | None,
        approver_id: uuid.UUID | None,
    ) -> HrVacationRequest:
        r = await VacationRequestsService.get(db, org_id, rid)
        if r.status != "pending":
            raise ValidationError(f"Solo se pueden aprobar solicitudes en 'pending' (actual: {r.status}).")
        r.status = "approved"
        r.approved_at = _now()
        r.approved_by = approver_id
        if notes:
            r.notes = (r.notes or "") + ("\n" if r.notes else "") + notes

        # Mover de pending a taken/compensated
        period = r.start_date.year
        bal = await VacationBalancesService._get_or_create(db, org_id, r.employee_id, period)
        amt = Decimal(r.days_count)
        bal.days_pending = max(Decimal("0"), Decimal(bal.days_pending or 0) - amt)
        if r.request_type == "paid":
            bal.days_taken = Decimal(bal.days_taken or 0) + amt
        elif r.request_type == "compensation":
            bal.days_compensated = Decimal(bal.days_compensated or 0) + amt

        await db.flush()
        await db.refresh(r)
        return r

    @staticmethod
    async def reject(
        db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID, reason: str,
        rejecter_id: uuid.UUID | None,
    ) -> HrVacationRequest:
        r = await VacationRequestsService.get(db, org_id, rid)
        if r.status != "pending":
            raise ValidationError(f"Solo se pueden rechazar solicitudes en 'pending' (actual: {r.status}).")
        r.status = "rejected"
        r.rejected_at = _now()
        r.rejected_by = rejecter_id
        r.rejection_reason = reason

        # Liberar pending
        period = r.start_date.year
        bal = await VacationBalancesService._get_or_create(db, org_id, r.employee_id, period)
        bal.days_pending = max(Decimal("0"), Decimal(bal.days_pending or 0) - Decimal(r.days_count))

        await db.flush()
        await db.refresh(r)
        return r

    @staticmethod
    async def cancel(
        db: AsyncSession, org_id: uuid.UUID, rid: uuid.UUID,
    ) -> HrVacationRequest:
        r = await VacationRequestsService.get(db, org_id, rid)
        if r.status not in ("pending", "approved"):
            raise ValidationError(f"No se puede cancelar una solicitud en '{r.status}'.")

        # Revertir saldo según estado actual
        period = r.start_date.year
        bal = await VacationBalancesService._get_or_create(db, org_id, r.employee_id, period)
        amt = Decimal(r.days_count)
        if r.status == "pending":
            bal.days_pending = max(Decimal("0"), Decimal(bal.days_pending or 0) - amt)
        elif r.status == "approved":
            if r.request_type == "paid":
                bal.days_taken = max(Decimal("0"), Decimal(bal.days_taken or 0) - amt)
            elif r.request_type == "compensation":
                bal.days_compensated = max(Decimal("0"), Decimal(bal.days_compensated or 0) - amt)

        r.status = "cancelled"
        r.cancelled_at = _now()
        await db.flush()
        await db.refresh(r)
        return r


# ============================================================ Leaves


class LeavesService:

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID,
        *, employee_id: uuid.UUID | None = None, leave_type: str | None = None,
        status: str | None = None,
    ) -> list[HrLeave]:
        stmt = (
            select(HrLeave)
            .where(HrLeave.organization_id == org_id)
            .order_by(HrLeave.start_date.desc())
        )
        if employee_id:
            stmt = stmt.where(HrLeave.employee_id == employee_id)
        if leave_type:
            stmt = stmt.where(HrLeave.leave_type == leave_type)
        if status:
            stmt = stmt.where(HrLeave.status == status)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, lid: uuid.UUID) -> HrLeave:
        leave = await db.scalar(
            select(HrLeave).where(HrLeave.id == lid, HrLeave.organization_id == org_id)
        )
        if leave is None:
            raise NotFoundError("Incapacidad/licencia no encontrada.")
        return leave

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: LeaveCreate, created_by: uuid.UUID | None,
    ) -> HrLeave:
        emp = await db.scalar(
            select(HrEmployee).where(
                HrEmployee.id == data.employee_id, HrEmployee.organization_id == org_id,
            )
        )
        if emp is None:
            raise NotFoundError("Empleado no encontrado.")
        number = await _next_leave_number(db, org_id)
        leave = HrLeave(
            organization_id=org_id,
            leave_number=number,
            status="active",
            created_by=created_by,
            **data.model_dump(),
        )
        db.add(leave)
        await db.flush()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, lid: uuid.UUID, data: LeaveUpdate,
    ) -> HrLeave:
        leave = await LeavesService.get(db, org_id, lid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(leave, k, v)
        await db.flush()
        await db.refresh(leave)
        return leave

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, lid: uuid.UUID) -> None:
        leave = await LeavesService.get(db, org_id, lid)
        await db.delete(leave)
        await db.flush()
