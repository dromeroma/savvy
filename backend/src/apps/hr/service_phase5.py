"""SavvyHR · service fase 5 — settings + liquidación."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hr.liquidation_engine import LiquidationResult, calculate_liquidation
from src.apps.hr.models import (
    HrContract,
    HrEmployee,
    HrLiquidation,
    HrLiquidationItem,
    HrSettings,
    HrVacationBalance,
    HrPayrollPeriod,
    HrPayroll,
)
from src.apps.hr.schemas import (
    HrSettingsResponse,
    HrSettingsUpdate,
    LiquidationCalculationInput,
    LiquidationCreate,
    LiquidationItemEdit,
    LiquidationItemSchema,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


def _now() -> datetime:
    return datetime.now(UTC)


# ============================================================ Settings


class HrSettingsService:

    @staticmethod
    async def get_or_create(db: AsyncSession, org_id: uuid.UUID) -> HrSettings:
        row = (await db.execute(
            select(HrSettings).where(HrSettings.organization_id == org_id)
        )).scalar_one_or_none()
        if row is None:
            row = HrSettings(organization_id=org_id, default_liquidation_template="formal")
            db.add(row)
            await db.flush()
        return row

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, data: HrSettingsUpdate,
    ) -> HrSettings:
        row = await HrSettingsService.get_or_create(db, org_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(row, k, v)
        row.updated_at = _now()
        await db.flush()
        await db.commit()
        return row


# ============================================================ Liquidation


class LiquidationsService:

    @staticmethod
    async def _employee_context(
        db: AsyncSession, org_id: uuid.UUID, employee_id: uuid.UUID,
    ) -> tuple[HrEmployee, HrContract]:
        emp = (await db.execute(
            select(HrEmployee).where(
                HrEmployee.id == employee_id,
                HrEmployee.organization_id == org_id,
            )
        )).scalar_one_or_none()
        if emp is None:
            raise NotFoundError("Empleado no encontrado")
        contract = (await db.execute(
            select(HrContract)
            .where(HrContract.employee_id == employee_id)
            .order_by(HrContract.start_date.desc())
            .limit(1)
        )).scalar_one_or_none()
        if contract is None:
            raise NotFoundError("El empleado no tiene contratos registrados")
        return emp, contract

    @staticmethod
    async def _vacation_days_pending(
        db: AsyncSession, employee_id: uuid.UUID,
    ) -> Decimal:
        rows = (await db.execute(
            select(HrVacationBalance).where(HrVacationBalance.employee_id == employee_id)
        )).scalars().all()
        total = Decimal("0")
        for r in rows:
            avail = (r.days_accrued or Decimal("0")) - (r.days_taken or Decimal("0")) \
                - (r.days_pending or Decimal("0")) - (r.days_compensated or Decimal("0"))
            if avail > 0:
                total += avail
        return total

    @staticmethod
    async def calculate(
        db: AsyncSession, org_id: uuid.UUID, data: LiquidationCalculationInput,
    ) -> LiquidationResult:
        emp, contract = await LiquidationsService._employee_context(db, org_id, data.employee_id)
        last_worked = data.last_worked_date or data.termination_date
        vac_pending = data.vacation_days_pending or \
            await LiquidationsService._vacation_days_pending(db, emp.id)
        return calculate_liquidation(
            contract_start_date=contract.start_date,
            termination_date=data.termination_date,
            last_worked_date=last_worked,
            termination_reason=data.termination_reason,
            base_salary=Decimal(contract.base_salary or 0),
            transport_allowance=Decimal(contract.transport_allowance or 0),
            has_legal_protection=data.has_legal_protection,
            pending_period_days=data.pending_period_days,
            vacation_days_pending=vac_pending,
        )

    @staticmethod
    async def _next_number(db: AsyncSession, org_id: uuid.UUID) -> str:
        prefix = f"LIQ-{_now().year}-"
        count = (await db.execute(
            select(HrLiquidation).where(
                HrLiquidation.organization_id == org_id,
                HrLiquidation.liquidation_number.like(f"{prefix}%"),
            )
        )).scalars().all()
        return f"{prefix}{len(count) + 1:04d}"

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: LiquidationCreate,
        *, created_by: uuid.UUID | None = None,
    ) -> HrLiquidation:
        emp, contract = await LiquidationsService._employee_context(db, org_id, data.employee_id)

        # Cálculo base
        calc_input = LiquidationCalculationInput(
            employee_id=data.employee_id,
            termination_date=data.termination_date,
            termination_reason=data.termination_reason,
            last_worked_date=data.last_worked_date,
            pending_period_days=data.pending_period_days,
            vacation_days_pending=data.vacation_days_pending,
            has_legal_protection=data.has_legal_protection,
        )
        calc = await LiquidationsService.calculate(db, org_id, calc_input)

        liq_number = await LiquidationsService._next_number(db, org_id)

        liq = HrLiquidation(
            organization_id=org_id,
            employee_id=emp.id,
            contract_id=contract.id,
            liquidation_number=liq_number,
            termination_date=calc.termination_date,
            termination_reason=calc.termination_reason,
            last_worked_date=calc.last_worked_date,
            contract_start_date=calc.contract_start_date,
            base_salary=calc.base_salary,
            average_salary=calc.average_salary,
            days_worked_total=calc.days_worked_total,
            total_earnings=calc.total_earnings,
            total_deductions=calc.total_deductions,
            net_amount=calc.net_amount,
            status="draft",
            notes=data.notes,
            pdf_template=data.pdf_template,
            created_by=created_by,
        )
        db.add(liq)
        await db.flush()

        items_to_insert = data.items_override or [
            LiquidationItemSchema(
                concept_code=it.code, concept_name=it.name,
                kind=it.kind, quantity=it.quantity,
                base_amount=it.base_amount, rate=it.rate,
                amount=it.amount, sort_order=it.sort_order,
                notes=it.notes, is_manual=False,
            ) for it in calc.items
        ]
        for it in items_to_insert:
            db.add(HrLiquidationItem(
                organization_id=org_id,
                liquidation_id=liq.id,
                concept_code=it.concept_code,
                concept_name=it.concept_name,
                kind=it.kind,
                quantity=Decimal(it.quantity),
                base_amount=Decimal(it.base_amount),
                rate=Decimal(it.rate) if it.rate is not None else None,
                amount=Decimal(it.amount),
                is_manual=it.is_manual,
                sort_order=it.sort_order,
                notes=it.notes,
            ))

        if data.items_override:
            earnings = sum((Decimal(i.amount) for i in data.items_override if i.kind == "earning"), Decimal("0"))
            deductions = sum((Decimal(i.amount) for i in data.items_override if i.kind == "deduction"), Decimal("0"))
            liq.total_earnings = earnings
            liq.total_deductions = deductions
            liq.net_amount = earnings - deductions

        await db.commit()
        await db.refresh(liq)
        return liq

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID,
        *, status: str | None = None, employee_id: uuid.UUID | None = None,
    ) -> list[tuple[HrLiquidation, HrEmployee]]:
        stmt = (
            select(HrLiquidation, HrEmployee)
            .join(HrEmployee, HrEmployee.id == HrLiquidation.employee_id)
            .where(HrLiquidation.organization_id == org_id)
            .order_by(HrLiquidation.created_at.desc())
        )
        if status:
            stmt = stmt.where(HrLiquidation.status == status)
        if employee_id:
            stmt = stmt.where(HrLiquidation.employee_id == employee_id)
        rows = await db.execute(stmt)
        return list(rows.all())

    @staticmethod
    async def get(
        db: AsyncSession, org_id: uuid.UUID, liq_id: uuid.UUID,
    ) -> HrLiquidation:
        row = (await db.execute(
            select(HrLiquidation).where(
                HrLiquidation.id == liq_id,
                HrLiquidation.organization_id == org_id,
            )
        )).scalar_one_or_none()
        if row is None:
            raise NotFoundError("Liquidación no encontrada")
        return row

    @staticmethod
    async def get_items(db: AsyncSession, liq_id: uuid.UUID) -> list[HrLiquidationItem]:
        rows = await db.execute(
            select(HrLiquidationItem)
            .where(HrLiquidationItem.liquidation_id == liq_id)
            .order_by(HrLiquidationItem.sort_order, HrLiquidationItem.concept_code)
        )
        return list(rows.scalars().all())

    @staticmethod
    async def edit_items(
        db: AsyncSession, org_id: uuid.UUID, liq_id: uuid.UUID, data: LiquidationItemEdit,
    ) -> HrLiquidation:
        liq = await LiquidationsService.get(db, org_id, liq_id)
        if liq.status != "draft":
            raise ConflictError("Solo se pueden editar liquidaciones en borrador")

        # Borrar ítems actuales y reinsertar
        old = await LiquidationsService.get_items(db, liq_id)
        for it in old:
            await db.delete(it)
        await db.flush()

        for it in data.items:
            db.add(HrLiquidationItem(
                organization_id=org_id,
                liquidation_id=liq.id,
                concept_code=it.concept_code,
                concept_name=it.concept_name,
                kind=it.kind,
                quantity=Decimal(it.quantity),
                base_amount=Decimal(it.base_amount),
                rate=Decimal(it.rate) if it.rate is not None else None,
                amount=Decimal(it.amount),
                is_manual=it.is_manual,
                sort_order=it.sort_order,
                notes=it.notes,
            ))

        earnings = sum((Decimal(i.amount) for i in data.items if i.kind == "earning"), Decimal("0"))
        deductions = sum((Decimal(i.amount) for i in data.items if i.kind == "deduction"), Decimal("0"))
        liq.total_earnings = earnings
        liq.total_deductions = deductions
        liq.net_amount = earnings - deductions
        if data.notes is not None:
            liq.notes = data.notes
        if data.pdf_template is not None:
            liq.pdf_template = data.pdf_template
        liq.updated_at = _now()
        await db.commit()
        await db.refresh(liq)
        return liq

    @staticmethod
    async def finalize(
        db: AsyncSession, org_id: uuid.UUID, liq_id: uuid.UUID,
        *, finalized_by: uuid.UUID | None = None,
    ) -> HrLiquidation:
        liq = await LiquidationsService.get(db, org_id, liq_id)
        if liq.status != "draft":
            raise ConflictError("Solo se pueden finalizar liquidaciones en borrador")
        liq.status = "finalized"
        liq.finalized_at = _now()
        liq.finalized_by = finalized_by
        await db.commit()
        await db.refresh(liq)
        return liq

    @staticmethod
    async def mark_paid(
        db: AsyncSession, org_id: uuid.UUID, liq_id: uuid.UUID,
    ) -> HrLiquidation:
        liq = await LiquidationsService.get(db, org_id, liq_id)
        if liq.status not in ("finalized",):
            raise ConflictError("Solo liquidaciones finalizadas se pueden marcar como pagadas")
        liq.status = "paid"
        liq.paid_at = _now()
        await db.commit()
        await db.refresh(liq)
        return liq
