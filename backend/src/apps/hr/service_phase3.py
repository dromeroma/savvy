"""SavvyHR · service fase 3 — concepts + periods + payrolls.

Acciones clave del período:
  - draft → calculate → calculated → approve → pay → close
"""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.apps.hr.models import (
    HrContract,
    HrEmployee,
    HrPayroll,
    HrPayrollConcept,
    HrPayrollItem,
    HrPayrollPeriod,
)
from src.apps.hr.payroll_engine import calculate_employee_payroll
from src.apps.hr.schemas import (
    PayrollConceptCreate,
    PayrollConceptUpdate,
    PayrollPeriodCreate,
    PayrollPeriodUpdate,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


def _now() -> datetime:
    return datetime.now(UTC)


# ============================================================ Concepts


class PayrollConceptsService:

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID,
        *, active_only: bool = False, concept_type: str | None = None,
    ) -> list[HrPayrollConcept]:
        stmt = (
            select(HrPayrollConcept)
            .where(HrPayrollConcept.organization_id == org_id)
            .order_by(HrPayrollConcept.sort_order, HrPayrollConcept.code)
        )
        if active_only:
            stmt = stmt.where(HrPayrollConcept.is_active.is_(True))
        if concept_type:
            stmt = stmt.where(HrPayrollConcept.concept_type == concept_type)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID) -> HrPayrollConcept:
        c = await db.scalar(
            select(HrPayrollConcept).where(
                HrPayrollConcept.id == cid,
                HrPayrollConcept.organization_id == org_id,
            )
        )
        if c is None:
            raise NotFoundError("Concepto no encontrado.")
        return c

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: PayrollConceptCreate,
    ) -> HrPayrollConcept:
        existing = await db.scalar(
            select(HrPayrollConcept).where(
                HrPayrollConcept.organization_id == org_id,
                HrPayrollConcept.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un concepto con código '{data.code}'.")
        c = HrPayrollConcept(organization_id=org_id, **data.model_dump())
        db.add(c)
        await db.flush()
        await db.refresh(c)
        return c

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID, data: PayrollConceptUpdate,
    ) -> HrPayrollConcept:
        c = await PayrollConceptsService.get(db, org_id, cid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(c, k, v)
        await db.flush()
        await db.refresh(c)
        return c

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID) -> None:
        c = await PayrollConceptsService.get(db, org_id, cid)
        await db.delete(c)
        await db.flush()

    # ---------------- Template Colombia ----------------

    COLOMBIA_TEMPLATE: list[dict] = [
        # ------- Earnings -------
        {"code": "SALARIO", "name": "Salario base", "concept_type": "earning",
         "category": "salary", "calculation_method": "formula",
         "formula": "daily_base", "sort_order": 10, "is_taxable": True},
        {"code": "AUX_TRANS", "name": "Auxilio de transporte", "concept_type": "earning",
         "category": "allowance", "calculation_method": "formula",
         "formula": "transport_allowance", "sort_order": 20, "is_taxable": False},
        {"code": "AUX_ALIM", "name": "Auxilio de alimentación", "concept_type": "earning",
         "category": "allowance", "calculation_method": "formula",
         "formula": "food_allowance", "sort_order": 21, "is_taxable": False},
        {"code": "AUX_CONNECT", "name": "Auxilio de conectividad", "concept_type": "earning",
         "category": "allowance", "calculation_method": "formula",
         "formula": "connectivity_allowance", "sort_order": 22, "is_taxable": False},
        {"code": "HE_DIURNA", "name": "Horas extra diurnas (25%)", "concept_type": "earning",
         "category": "overtime", "calculation_method": "quantity_rate",
         "sort_order": 30, "is_taxable": True},
        {"code": "HE_NOCTURNA", "name": "Horas extra nocturnas (75%)", "concept_type": "earning",
         "category": "overtime", "calculation_method": "quantity_rate",
         "sort_order": 31, "is_taxable": True},
        {"code": "HE_DOMINICAL", "name": "Recargo dominical/festivo (100%)", "concept_type": "earning",
         "category": "overtime", "calculation_method": "quantity_rate",
         "sort_order": 32, "is_taxable": True},
        # ------- Deductions -------
        {"code": "SALUD_EMP", "name": "Aporte salud empleado (4%)", "concept_type": "deduction",
         "category": "health", "calculation_method": "percentage",
         "percentage_value": Decimal("4"), "base_concept_code": "SALARIO",
         "sort_order": 100, "is_taxable": False},
        {"code": "PENSION_EMP", "name": "Aporte pensión empleado (4%)", "concept_type": "deduction",
         "category": "pension", "calculation_method": "percentage",
         "percentage_value": Decimal("4"), "base_concept_code": "SALARIO",
         "sort_order": 101, "is_taxable": False},
        {"code": "RETEFUENTE", "name": "Retención en la fuente", "concept_type": "deduction",
         "category": "tax", "calculation_method": "fixed",
         "fixed_value": Decimal("0"), "sort_order": 110, "is_taxable": False},
        # ------- Benefits (prestaciones sociales: provisión mensual) -------
        {"code": "CESANTIAS", "name": "Cesantías (8.33%)", "concept_type": "benefit",
         "category": "severance", "calculation_method": "percentage",
         "percentage_value": Decimal("8.33"), "base_concept_code": "SALARIO",
         "sort_order": 200, "is_taxable": False},
        {"code": "INT_CESANTIAS", "name": "Intereses cesantías (1%)", "concept_type": "benefit",
         "category": "cesantias_interest", "calculation_method": "percentage",
         "percentage_value": Decimal("1"), "base_concept_code": "CESANTIAS",
         "sort_order": 201, "is_taxable": False},
        {"code": "PRIMA", "name": "Prima de servicios (8.33%)", "concept_type": "benefit",
         "category": "service_bonus", "calculation_method": "percentage",
         "percentage_value": Decimal("8.33"), "base_concept_code": "SALARIO",
         "sort_order": 202, "is_taxable": False},
        {"code": "VACACIONES_PROV", "name": "Vacaciones provisión (4.17%)", "concept_type": "benefit",
         "category": "vacation", "calculation_method": "percentage",
         "percentage_value": Decimal("4.17"), "base_concept_code": "SALARIO",
         "sort_order": 203, "is_taxable": False},
        # ------- Employer contributions (aportes patronales) -------
        {"code": "SALUD_PAT", "name": "Salud patronal (8.5%)", "concept_type": "employer_contribution",
         "category": "health", "calculation_method": "percentage",
         "percentage_value": Decimal("8.5"), "base_concept_code": "SALARIO",
         "sort_order": 300, "is_taxable": False},
        {"code": "PENSION_PAT", "name": "Pensión patronal (12%)", "concept_type": "employer_contribution",
         "category": "pension", "calculation_method": "percentage",
         "percentage_value": Decimal("12"), "base_concept_code": "SALARIO",
         "sort_order": 301, "is_taxable": False},
        {"code": "ARL", "name": "ARL (riesgo I 0.522%)", "concept_type": "employer_contribution",
         "category": "arl", "calculation_method": "percentage",
         "percentage_value": Decimal("0.522"), "base_concept_code": "SALARIO",
         "sort_order": 302, "is_taxable": False},
        {"code": "CAJA", "name": "Caja de compensación (4%)", "concept_type": "employer_contribution",
         "category": "compensation_fund", "calculation_method": "percentage",
         "percentage_value": Decimal("4"), "base_concept_code": "SALARIO",
         "sort_order": 303, "is_taxable": False},
        {"code": "ICBF", "name": "ICBF (3%)", "concept_type": "employer_contribution",
         "category": "parafiscal", "calculation_method": "percentage",
         "percentage_value": Decimal("3"), "base_concept_code": "SALARIO",
         "sort_order": 304, "is_taxable": False},
        {"code": "SENA", "name": "SENA (2%)", "concept_type": "employer_contribution",
         "category": "parafiscal", "calculation_method": "percentage",
         "percentage_value": Decimal("2"), "base_concept_code": "SALARIO",
         "sort_order": 305, "is_taxable": False},
    ]

    @staticmethod
    async def seed_country_template(
        db: AsyncSession, org_id: uuid.UUID, country_code: str = "CO",
    ) -> int:
        """Carga template del país. Solo crea conceptos que no existen."""
        if country_code.upper() != "CO":
            raise ValidationError(
                f"Solo hay template para Colombia (CO). País solicitado: {country_code}",
            )
        created = 0
        for spec in PayrollConceptsService.COLOMBIA_TEMPLATE:
            existing = await db.scalar(
                select(HrPayrollConcept).where(
                    HrPayrollConcept.organization_id == org_id,
                    HrPayrollConcept.code == spec["code"],
                )
            )
            if existing is not None:
                continue
            c = HrPayrollConcept(
                organization_id=org_id,
                country_code="CO",
                is_active=True,
                **spec,
            )
            db.add(c)
            created += 1
        await db.flush()
        return created


# ============================================================ Periods


class PayrollPeriodsService:

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID,
        *, status: str | None = None, year: int | None = None,
    ) -> list[HrPayrollPeriod]:
        stmt = (
            select(HrPayrollPeriod)
            .where(HrPayrollPeriod.organization_id == org_id)
            .order_by(HrPayrollPeriod.start_date.desc())
        )
        if status:
            stmt = stmt.where(HrPayrollPeriod.status == status)
        if year is not None:
            from datetime import date as _date
            stmt = stmt.where(
                HrPayrollPeriod.start_date >= _date(year, 1, 1),
                HrPayrollPeriod.start_date <= _date(year, 12, 31),
            )
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID) -> HrPayrollPeriod:
        p = await db.scalar(
            select(HrPayrollPeriod).where(
                HrPayrollPeriod.id == pid,
                HrPayrollPeriod.organization_id == org_id,
            )
        )
        if p is None:
            raise NotFoundError("Período de nómina no encontrado.")
        return p

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: PayrollPeriodCreate,
        created_by: uuid.UUID | None,
    ) -> HrPayrollPeriod:
        existing = await db.scalar(
            select(HrPayrollPeriod).where(
                HrPayrollPeriod.organization_id == org_id,
                HrPayrollPeriod.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un período con código '{data.code}'.")
        p = HrPayrollPeriod(
            organization_id=org_id,
            status="draft",
            created_by=created_by,
            **data.model_dump(),
        )
        db.add(p)
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID, data: PayrollPeriodUpdate,
    ) -> HrPayrollPeriod:
        p = await PayrollPeriodsService.get(db, org_id, pid)
        if p.status not in ("draft", "calculated"):
            raise ValidationError(
                f"No se puede modificar un período en estado '{p.status}'.",
            )
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(p, k, v)
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID) -> None:
        p = await PayrollPeriodsService.get(db, org_id, pid)
        if p.status != "draft":
            raise ValidationError("Solo se pueden eliminar períodos en estado 'draft'.")
        await db.delete(p)
        await db.flush()

    # ---------------- Calcular ----------------

    @staticmethod
    async def calculate(
        db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID,
    ) -> dict:
        period = await PayrollPeriodsService.get(db, org_id, pid)
        if period.status not in ("draft", "calculated"):
            raise ValidationError(
                f"No se puede recalcular un período en estado '{period.status}'.",
            )

        # Conceptos activos
        concepts_rows = await db.execute(
            select(HrPayrollConcept).where(
                HrPayrollConcept.organization_id == org_id,
                HrPayrollConcept.is_active.is_(True),
            )
        )
        concepts = list(concepts_rows.scalars().all())
        if not concepts:
            raise ValidationError(
                "No hay conceptos de nómina configurados. Carga el template del país primero.",
            )

        # Empleados activos
        emp_rows = await db.execute(
            select(HrEmployee).where(
                HrEmployee.organization_id == org_id,
                HrEmployee.status == "active",
            )
        )
        employees = list(emp_rows.scalars().all())

        # Borrar liquidaciones previas del período (recálculo limpio)
        from sqlalchemy import delete as _delete
        prev_payrolls = await db.execute(
            select(HrPayroll.id).where(HrPayroll.period_id == period.id)
        )
        prev_ids = [r[0] for r in prev_payrolls.all()]
        if prev_ids:
            await db.execute(_delete(HrPayrollItem).where(HrPayrollItem.payroll_id.in_(prev_ids)))
            await db.execute(_delete(HrPayroll).where(HrPayroll.id.in_(prev_ids)))

        period.status = "calculating"
        await db.flush()

        total_gross = Decimal("0")
        total_deductions = Decimal("0")
        total_net = Decimal("0")

        for emp in employees:
            # Contrato activo
            contract = await db.scalar(
                select(HrContract).where(
                    HrContract.organization_id == org_id,
                    HrContract.employee_id == emp.id,
                    HrContract.status == "active",
                ).order_by(HrContract.start_date.desc()).limit(1)
            )

            calc = await calculate_employee_payroll(
                db, org_id, emp, contract,
                period.start_date, period.end_date,
                concepts,
            )

            payroll = HrPayroll(
                organization_id=org_id,
                period_id=period.id,
                employee_id=emp.id,
                contract_id=calc.contract_id,
                employee_code=calc.employee_code,
                employee_name=calc.employee_name,
                department_name=calc.department_name,
                position_name=calc.position_name,
                base_salary=calc.base_salary,
                worked_days=calc.worked_days,
                absence_days=calc.absence_days,
                total_earnings=calc.total_earnings,
                total_deductions=calc.total_deductions,
                total_benefits=calc.total_benefits,
                total_employer_contrib=calc.total_employer_contrib,
                net_amount=calc.net_amount,
                status="calculated",
            )
            db.add(payroll)
            await db.flush()

            for item in calc.items:
                db.add(HrPayrollItem(
                    payroll_id=payroll.id,
                    concept_id=item.concept_id,
                    concept_code=item.concept_code,
                    concept_name=item.concept_name,
                    concept_type=item.concept_type,
                    category=item.category,
                    quantity=item.quantity,
                    rate=item.rate,
                    base_amount=item.base_amount,
                    percentage=item.percentage,
                    amount=item.amount,
                    sort_order=item.sort_order,
                ))

            total_gross += calc.total_earnings
            total_deductions += calc.total_deductions
            total_net += calc.net_amount

        period.status = "calculated"
        period.calculated_at = _now()
        period.total_gross = total_gross
        period.total_deductions = total_deductions
        period.total_net = total_net
        period.employee_count = len(employees)

        await db.flush()
        await db.refresh(period)
        return {
            "period_id": period.id,
            "employees_processed": len(employees),
            "total_gross": total_gross,
            "total_deductions": total_deductions,
            "total_net": total_net,
        }

    @staticmethod
    async def approve(
        db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID, approver: uuid.UUID | None,
    ) -> HrPayrollPeriod:
        p = await PayrollPeriodsService.get(db, org_id, pid)
        if p.status != "calculated":
            raise ValidationError(f"No se puede aprobar un período en estado '{p.status}'.")
        p.status = "approved"
        p.approved_at = _now()
        p.approved_by = approver
        # Actualizar status de payrolls
        from sqlalchemy import update as _update
        await db.execute(
            _update(HrPayroll)
            .where(HrPayroll.period_id == p.id)
            .values(status="approved")
        )
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def pay(
        db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID,
        payer: uuid.UUID | None,
        payment_reference: str | None = None,
        create_finance_transaction: bool = True,
    ) -> HrPayrollPeriod:
        p = await PayrollPeriodsService.get(db, org_id, pid)
        if p.status != "approved":
            raise ValidationError(
                f"Solo se puede pagar un período aprobado (actual: '{p.status}').",
            )
        p.status = "paid"
        p.paid_at = _now()
        p.paid_by = payer

        from sqlalchemy import update as _update
        await db.execute(
            _update(HrPayroll)
            .where(HrPayroll.period_id == p.id)
            .values(status="paid", paid_at=_now(), payment_reference=payment_reference)
        )

        if create_finance_transaction:
            await _create_finance_transaction(db, org_id, p)

        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def close(
        db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID,
    ) -> HrPayrollPeriod:
        p = await PayrollPeriodsService.get(db, org_id, pid)
        if p.status != "paid":
            raise ValidationError(
                f"Solo se puede cerrar un período pagado (actual: '{p.status}').",
            )
        p.status = "closed"
        p.closed_at = _now()
        await db.flush()
        await db.refresh(p)
        return p


# ============================================================ Payrolls (queries)


class PayrollsService:

    @staticmethod
    async def list_by_period(
        db: AsyncSession, org_id: uuid.UUID, period_id: uuid.UUID,
    ) -> list[HrPayroll]:
        rows = await db.execute(
            select(HrPayroll)
            .where(
                HrPayroll.organization_id == org_id,
                HrPayroll.period_id == period_id,
            )
            .order_by(HrPayroll.employee_code)
        )
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID) -> HrPayroll:
        p = await db.scalar(
            select(HrPayroll).where(
                HrPayroll.id == pid,
                HrPayroll.organization_id == org_id,
            )
        )
        if p is None:
            raise NotFoundError("Liquidación no encontrada.")
        return p

    @staticmethod
    async def get_items(
        db: AsyncSession, payroll_id: uuid.UUID,
    ) -> list[HrPayrollItem]:
        rows = await db.execute(
            select(HrPayrollItem)
            .where(HrPayrollItem.payroll_id == payroll_id)
            .order_by(HrPayrollItem.sort_order, HrPayrollItem.concept_code)
        )
        return list(rows.scalars().all())


# ============================================================ Integration: finance


async def _create_finance_transaction(
    db: AsyncSession, org_id: uuid.UUID, period: HrPayrollPeriod,
) -> None:
    """Crea una FinanceTransaction de egreso por el total neto del período.

    Best-effort: si la tabla no existe o el módulo finance no está activo,
    se ignora.
    """
    try:
        from src.modules.finance.models import FinanceTransaction
        tx = FinanceTransaction(
            organization_id=org_id,
            type="expense",
            amount=period.total_net,
            date=period.payment_date or period.end_date,
            description=f"Nómina · período {period.code}",
            reference_type="hr_payroll_period",
            reference_id=period.id,
            app_code="hr",
        )
        db.add(tx)
        await db.flush()
    except Exception:
        # Finance no disponible o esquema distinto — no es crítico
        pass
