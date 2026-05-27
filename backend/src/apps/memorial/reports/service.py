"""Reportes y analytics de SavvyMemorial."""

from __future__ import annotations

import uuid
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.models import (
    MemorialAttendance,
    MemorialEmployee,
    MemorialExequialContract,
    MemorialExequialPlan,
    MemorialInventoryItem,
    MemorialInvoice,
    MemorialLead,
    MemorialPayment,
    MemorialPaymentInvoice,
    MemorialPosition,
    MemorialService,
)
from src.apps.memorial.reports.schemas import (
    EmployeeRankingItem,
    EmployeeRankingReport,
    IncomePoint,
    IncomeReport,
    OperationalKpis,
    PlanRankingItem,
    PlanRankingReport,
    ServiceTypeCount,
    ServicesByTypeReport,
)


def _default_range() -> tuple[date, date]:
    today = date.today()
    start = today.replace(day=1) - timedelta(days=365)
    return start.replace(day=1), today


def _coerce_dates(date_from: date | None, date_to: date | None) -> tuple[date, date]:
    if date_from and date_to:
        return date_from, date_to
    df, dt = _default_range()
    return date_from or df, date_to or dt


class ReportsService:

    # -------------------- Ingresos por período --------------------

    @staticmethod
    async def income_report(
        db: AsyncSession, org_id: uuid.UUID,
        date_from: date | None = None, date_to: date | None = None,
    ) -> IncomeReport:
        df, dt = _coerce_dates(date_from, date_to)

        period = func.to_char(MemorialPayment.payment_date, "YYYY-MM").label("period")
        applied_dues = func.sum(
            case(
                (MemorialInvoice.source_type == "exequial_dues", MemorialPaymentInvoice.amount),
                else_=0,
            )
        ).label("dues_total")
        applied_service = func.sum(
            case(
                (MemorialInvoice.source_type == "service", MemorialPaymentInvoice.amount),
                else_=0,
            )
        ).label("service_total")

        # Aggregate by (period, source_type) via payment_invoices join
        stmt = (
            select(period, applied_dues, applied_service)
            .select_from(MemorialPayment)
            .join(MemorialPaymentInvoice, MemorialPaymentInvoice.payment_id == MemorialPayment.id)
            .join(MemorialInvoice, MemorialInvoice.id == MemorialPaymentInvoice.invoice_id)
            .where(
                MemorialPayment.organization_id == org_id,
                MemorialPayment.payment_date >= df,
                MemorialPayment.payment_date <= dt,
            )
            .group_by(period)
            .order_by(period)
        )
        rows = (await db.execute(stmt)).all()

        points: list[IncomePoint] = []
        total_dues = Decimal("0")
        total_services = Decimal("0")
        for r in rows:
            dues = Decimal(r.dues_total or 0)
            svc = Decimal(r.service_total or 0)
            points.append(IncomePoint(
                period=r.period, exequial_dues=dues, service_income=svc, total=dues + svc,
            ))
            total_dues += dues
            total_services += svc

        return IncomeReport(
            date_from=df, date_to=dt, points=points,
            total_dues=total_dues, total_services=total_services,
            grand_total=total_dues + total_services,
        )

    # -------------------- Servicios por tipo --------------------

    @staticmethod
    async def services_by_type(
        db: AsyncSession, org_id: uuid.UUID,
        date_from: date | None = None, date_to: date | None = None,
    ) -> ServicesByTypeReport:
        df, dt = _coerce_dates(date_from, date_to)
        stmt = (
            select(
                MemorialService.service_type,
                func.count(MemorialService.id).label("count"),
                func.coalesce(func.sum(MemorialService.final_total), 0).label("revenue"),
            )
            .where(
                MemorialService.organization_id == org_id,
                MemorialService.deceased_death_date >= df,
                MemorialService.deceased_death_date <= dt,
            )
            .group_by(MemorialService.service_type)
            .order_by(func.count(MemorialService.id).desc())
        )
        rows = (await db.execute(stmt)).all()
        items = [
            ServiceTypeCount(
                service_type=r.service_type,
                count=int(r.count),
                total_revenue=Decimal(r.revenue or 0),
            )
            for r in rows
        ]
        return ServicesByTypeReport(
            date_from=df, date_to=dt,
            items=items,
            total_count=sum(i.count for i in items),
            total_revenue=sum((i.total_revenue for i in items), Decimal("0")),
        )

    # -------------------- Ranking planes --------------------

    @staticmethod
    async def plan_ranking(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> PlanRankingReport:
        stmt = (
            select(
                MemorialExequialPlan.id,
                MemorialExequialPlan.code,
                MemorialExequialPlan.name,
                func.count(MemorialExequialContract.id).label("contracts_count"),
                func.sum(
                    case(
                        (MemorialExequialContract.status == "active", 1),
                        else_=0,
                    )
                ).label("active_count"),
                func.coalesce(func.sum(MemorialExequialContract.fee_amount), 0).label("revenue"),
            )
            .select_from(MemorialExequialPlan)
            .outerjoin(
                MemorialExequialContract,
                and_(
                    MemorialExequialContract.plan_id == MemorialExequialPlan.id,
                    MemorialExequialContract.organization_id == org_id,
                ),
            )
            .where(MemorialExequialPlan.organization_id == org_id)
            .group_by(MemorialExequialPlan.id, MemorialExequialPlan.code, MemorialExequialPlan.name)
            .order_by(func.count(MemorialExequialContract.id).desc())
        )
        rows = (await db.execute(stmt)).all()
        items = [
            PlanRankingItem(
                plan_id=r.id, plan_code=r.code, plan_name=r.name,
                contracts_count=int(r.contracts_count or 0),
                active_count=int(r.active_count or 0),
                total_revenue=Decimal(r.revenue or 0),
            )
            for r in rows
        ]
        return PlanRankingReport(items=items)

    # -------------------- Ranking empleados (por asistencia) --------------------

    @staticmethod
    async def employee_ranking(
        db: AsyncSession, org_id: uuid.UUID,
        date_from: date | None = None, date_to: date | None = None,
    ) -> EmployeeRankingReport:
        df, dt = _coerce_dates(date_from, date_to)
        stmt = (
            select(
                MemorialEmployee.id,
                MemorialEmployee.code,
                MemorialEmployee.first_name,
                MemorialEmployee.last_name,
                MemorialPosition.name.label("position_name"),
                func.sum(
                    case(
                        (MemorialAttendance.status == "present", 1),
                        else_=0,
                    )
                ).label("days_present"),
                func.coalesce(func.sum(MemorialAttendance.hours_worked), 0).label("hours_worked"),
            )
            .select_from(MemorialEmployee)
            .outerjoin(
                MemorialAttendance,
                and_(
                    MemorialAttendance.employee_id == MemorialEmployee.id,
                    MemorialAttendance.work_date >= df,
                    MemorialAttendance.work_date <= dt,
                ),
            )
            .outerjoin(
                MemorialPosition,
                MemorialPosition.id == MemorialEmployee.position_id,
            )
            .where(MemorialEmployee.organization_id == org_id)
            .group_by(
                MemorialEmployee.id, MemorialEmployee.code,
                MemorialEmployee.first_name, MemorialEmployee.last_name,
                MemorialPosition.name,
            )
            .order_by(func.coalesce(func.sum(MemorialAttendance.hours_worked), 0).desc())
        )
        rows = (await db.execute(stmt)).all()
        items = [
            EmployeeRankingItem(
                employee_id=r.id,
                employee_code=r.code,
                employee_name=f"{r.first_name} {r.last_name or ''}".strip(),
                position_name=r.position_name,
                days_present=int(r.days_present or 0),
                hours_worked=Decimal(r.hours_worked or 0),
            )
            for r in rows
        ]
        return EmployeeRankingReport(date_from=df, date_to=dt, items=items)

    # -------------------- KPIs operacionales --------------------

    @staticmethod
    async def operational_kpis(
        db: AsyncSession, org_id: uuid.UUID,
        days: int = 30,
    ) -> OperationalKpis:
        period_start = datetime.now(timezone.utc) - timedelta(days=days)

        services_open = await db.scalar(
            select(func.count(MemorialService.id)).where(
                MemorialService.organization_id == org_id,
                MemorialService.status == "iniciado",
            )
        ) or 0

        services_in_progress = await db.scalar(
            select(func.count(MemorialService.id)).where(
                MemorialService.organization_id == org_id,
                MemorialService.status.in_(["en_proceso", "pendiente"]),
            )
        ) or 0

        services_closed = await db.scalar(
            select(func.count(MemorialService.id)).where(
                MemorialService.organization_id == org_id,
                MemorialService.status == "finalizado",
                MemorialService.closed_at >= period_start,
            )
        ) or 0

        avg_secs = await db.scalar(
            select(
                func.avg(
                    func.extract("epoch", MemorialService.closed_at - MemorialService.created_at)
                )
            ).where(
                MemorialService.organization_id == org_id,
                MemorialService.status == "finalizado",
                MemorialService.closed_at.is_not(None),
                MemorialService.closed_at >= period_start,
            )
        )
        avg_close_hours = float(avg_secs) / 3600.0 if avg_secs else None

        contracts_active = await db.scalar(
            select(func.count(MemorialExequialContract.id)).where(
                MemorialExequialContract.organization_id == org_id,
                MemorialExequialContract.status == "active",
            )
        ) or 0

        contracts_overdue = await db.scalar(
            select(func.count(func.distinct(MemorialInvoice.contract_id))).where(
                MemorialInvoice.organization_id == org_id,
                MemorialInvoice.source_type == "exequial_dues",
                MemorialInvoice.status.in_(["pending", "partial", "overdue"]),
                MemorialInvoice.due_date < date.today(),
                MemorialInvoice.contract_id.is_not(None),
            )
        ) or 0

        leads_open = await db.scalar(
            select(func.count(MemorialLead.id)).where(
                MemorialLead.organization_id == org_id,
                MemorialLead.status.in_(["new", "contacted", "qualified", "proposal"]),
            )
        ) or 0

        leads_won = await db.scalar(
            select(func.count(MemorialLead.id)).where(
                MemorialLead.organization_id == org_id,
                MemorialLead.status == "won",
                MemorialLead.converted_at >= period_start,
            )
        ) or 0

        low_stock = await db.scalar(
            select(func.count(MemorialInventoryItem.id)).where(
                MemorialInventoryItem.organization_id == org_id,
                MemorialInventoryItem.is_active.is_(True),
                MemorialInventoryItem.current_stock <= MemorialInventoryItem.min_stock,
            )
        ) or 0

        return OperationalKpis(
            services_open=int(services_open),
            services_in_progress=int(services_in_progress),
            services_closed_period=int(services_closed),
            avg_close_hours=avg_close_hours,
            contracts_active=int(contracts_active),
            contracts_overdue=int(contracts_overdue),
            leads_open=int(leads_open),
            leads_won_period=int(leads_won),
            inventory_low_stock_items=int(low_stock),
        )
