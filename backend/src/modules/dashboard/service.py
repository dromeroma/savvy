"""Aggregates the org's identity + per-app KPIs for the dashboard view."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.congregants.models import ChurchCongregant
from src.core.exceptions import NotFoundError
from src.modules.apps.models import AppRegistry, AppUserRole, OrganizationApp
from src.modules.church_hierarchy.models import ChurchDenomination, ChurchZone
from src.modules.dashboard.schemas import (
    DashboardApp,
    DashboardExecutiveTotals,
    DashboardMetric,
    DashboardOrganization,
    DashboardSubscription,
    DashboardSummaryResponse,
)
from src.modules.finance.models import FinanceTransaction
from src.modules.organization.models import (
    BusinessTypeCatalog,
    Membership,
    Organization,
)
from src.modules.people.models import Person
from src.modules.platform.models import (
    OrganizationSubscription,
    SubscriptionPlan,
)


def _fmt_money(amount: Decimal | float | int | None) -> str:
    if amount is None:
        return "$ 0"
    n = float(amount)
    # Spanish-style integer with thousands separator
    return "$ " + f"{int(round(n)):,}".replace(",", ".")


def _fmt_int(n: int | None) -> str:
    if n is None:
        return "0"
    return f"{n:,}".replace(",", ".")


class DashboardService:

    @staticmethod
    async def get_summary(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> DashboardSummaryResponse:
        org = await db.get(Organization, org_id)
        if org is None or org.deleted_at is not None:
            raise NotFoundError("Organization not found.")

        org_data = await DashboardService._org_summary(db, org)
        subscription = await DashboardService._active_subscription(db, org_id)
        apps = await DashboardService._active_apps(db, org_id, user_id)
        metrics = await DashboardService._metrics(db, org_id, [a.code for a in apps])
        totals = DashboardService._executive_totals(metrics, len(apps))

        return DashboardSummaryResponse(
            organization=org_data,
            subscription=subscription,
            active_apps=apps,
            metrics=metrics,
            totals=totals,
        )

    # ------------------------------------------------------------------
    # Organization
    # ------------------------------------------------------------------
    @staticmethod
    async def _org_summary(db: AsyncSession, org: Organization) -> DashboardOrganization:
        # business_type label (from catalog)
        bt_label: str | None = None
        if org.business_type:
            bt = await db.scalar(
                select(BusinessTypeCatalog).where(BusinessTypeCatalog.code == org.business_type),
            )
            if bt is not None:
                bt_label = bt.name

        # Member count
        member_count = await db.scalar(
            select(func.count(Membership.id)).where(Membership.organization_id == org.id)
        ) or 0

        # Denomination + zone (for church)
        denomination_name: str | None = None
        zone_label: str | None = None
        if org.denomination_id:
            denom = await db.scalar(
                select(ChurchDenomination).where(ChurchDenomination.id == org.denomination_id),
            )
            if denom is not None:
                denomination_name = denom.name
        if org.zone_id:
            zone = await db.scalar(
                select(ChurchZone).where(ChurchZone.id == org.zone_id),
            )
            if zone is not None:
                parts = [f"Zona {zone.number}"]
                if zone.name:
                    parts.append(zone.name)
                zone_label = " — ".join(parts)

        return DashboardOrganization(
            id=org.id,
            name=org.name,
            slug=org.slug,
            type=org.type,
            business_type=org.business_type,
            business_type_label=bt_label,
            denomination_name=denomination_name,
            zone_label=zone_label,
            member_count=int(member_count),
            created_at=org.created_at,
        )

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------
    @staticmethod
    async def _active_subscription(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> DashboardSubscription | None:
        row = await db.execute(
            select(OrganizationSubscription, SubscriptionPlan)
            .join(SubscriptionPlan, SubscriptionPlan.id == OrganizationSubscription.plan_id)
            .where(
                OrganizationSubscription.organization_id == org_id,
                OrganizationSubscription.status.in_(["trial", "active", "past_due"]),
            )
            .order_by(OrganizationSubscription.started_at.desc())
            .limit(1)
        )
        result = row.first()
        if result is None:
            return None
        sub, plan = result
        return DashboardSubscription(
            plan_code=plan.code,
            plan_name=plan.name,
            status=sub.status,
            billing_cycle=sub.billing_cycle,
            started_at=sub.started_at.isoformat(),
            trial_ends_at=sub.trial_ends_at.isoformat() if sub.trial_ends_at else None,
        )

    # ------------------------------------------------------------------
    # Active apps
    # ------------------------------------------------------------------
    @staticmethod
    async def _active_apps(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> list[DashboardApp]:
        rows = await db.execute(
            select(OrganizationApp, AppRegistry, AppUserRole.role)
            .join(AppRegistry, AppRegistry.id == OrganizationApp.app_id)
            .outerjoin(
                AppUserRole,
                (AppUserRole.app_id == OrganizationApp.app_id)
                & (AppUserRole.organization_id == OrganizationApp.organization_id)
                & (AppUserRole.user_id == user_id),
            )
            .where(
                OrganizationApp.organization_id == org_id,
                OrganizationApp.status.in_(["active", "trial"]),
            )
            .order_by(AppRegistry.name)
        )
        return [
            DashboardApp(
                code=reg.code,
                name=reg.name,
                description=reg.description,
                icon=reg.icon,
                color=reg.color,
                status=org_app.status,
                user_role=role,
            )
            for org_app, reg, role in rows.all()
        ]

    # ------------------------------------------------------------------
    # Metrics dispatcher (per active app)
    # ------------------------------------------------------------------
    @staticmethod
    async def _metrics(
        db: AsyncSession,
        org_id: uuid.UUID,
        app_codes: list[str],
    ) -> list[DashboardMetric]:
        metrics: list[DashboardMetric] = []
        if "church" in app_codes:
            metrics.extend(await DashboardService._church_metrics(db, org_id))
        if "memorial" in app_codes:
            metrics.extend(await DashboardService._memorial_metrics(db, org_id))
        if "water" in app_codes:
            metrics.extend(await DashboardService._water_metrics(db, org_id))
        if "pos" in app_codes:
            metrics.extend(await DashboardService._pos_metrics(db, org_id))
        if "parking" in app_codes:
            metrics.extend(await DashboardService._parking_metrics(db, org_id))
        if "health" in app_codes:
            metrics.extend(await DashboardService._health_metrics(db, org_id))
        if "pay" in app_codes:
            metrics.extend(await DashboardService._pay_metrics(db, org_id))
        if "condo" in app_codes:
            metrics.extend(await DashboardService._condo_metrics(db, org_id))
        if "credit" in app_codes:
            metrics.extend(await DashboardService._credit_metrics(db, org_id))
        if "edu" in app_codes:
            metrics.extend(await DashboardService._edu_metrics(db, org_id))
        if "family" in app_codes:
            metrics.extend(await DashboardService._family_metrics(db, org_id))
        if "crm" in app_codes:
            metrics.extend(await DashboardService._crm_metrics(db, org_id))
        return metrics

    # ------------------------------------------------------------------
    # Executive totals (cross-app aggregation)
    # ------------------------------------------------------------------
    @staticmethod
    def _executive_totals(
        metrics: list[DashboardMetric],
        active_apps_count: int,
    ) -> DashboardExecutiveTotals:
        income = 0.0
        receivables = 0.0
        alerts = 0
        for m in metrics:
            if m.raw_value is None:
                continue
            if m.key.endswith(".income_month"):
                income += m.raw_value
            elif m.key.endswith(".receivables"):
                receivables += m.raw_value
            elif m.key.endswith(".alert"):
                alerts += int(m.raw_value)
        return DashboardExecutiveTotals(
            income_month=_fmt_money(income),
            income_month_raw=income,
            receivables_total=_fmt_money(receivables),
            receivables_total_raw=receivables,
            alerts_count=alerts,
            active_apps_count=active_apps_count,
        )

    @staticmethod
    async def _church_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        """Two headline KPIs only — full detail lives in /church/dashboard."""
        today = date.today()
        first_of_month = today.replace(day=1)

        active = await db.scalar(
            select(func.count(ChurchCongregant.id))
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(
                ChurchCongregant.organization_id == org_id,
                Person.status == "active",
            )
        ) or 0

        income = await db.scalar(
            select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
                FinanceTransaction.organization_id == org_id,
                FinanceTransaction.app_code == "church",
                FinanceTransaction.type == "income",
                FinanceTransaction.date >= first_of_month,
                FinanceTransaction.date <= today,
            )
        ) or 0

        return [
            DashboardMetric(
                key="church.active_congregants",
                label="Congregantes activos",
                value=_fmt_int(int(active)),
                raw_value=float(active),
                icon="users",
                color="#7C3AED",
                app_code="church",
            ),
            DashboardMetric(
                key="church.income_month",
                label="Ingresos del mes",
                value=_fmt_money(income),
                raw_value=float(income),
                icon="trending-up",
                color="#059669",
                app_code="church",
            ),
        ]

    # ------------------------------------------------------------------
    # Memorial KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _memorial_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from src.apps.memorial.models import (
            MemorialExequialContract,
            MemorialInvoice,
            MemorialPayment,
            MemorialService,
        )
        today = date.today()
        first_of_month = today.replace(day=1)

        services_open = await db.scalar(
            select(func.count(MemorialService.id)).where(
                MemorialService.organization_id == org_id,
                MemorialService.status.in_(["iniciado", "en_proceso", "pendiente"]),
            )
        ) or 0

        contracts_active = await db.scalar(
            select(func.count(MemorialExequialContract.id)).where(
                MemorialExequialContract.organization_id == org_id,
                MemorialExequialContract.status == "active",
            )
        ) or 0

        income = await db.scalar(
            select(func.coalesce(func.sum(MemorialPayment.amount), 0)).where(
                MemorialPayment.organization_id == org_id,
                MemorialPayment.payment_date >= first_of_month,
                MemorialPayment.payment_date <= today,
            )
        ) or 0

        receivables = await db.scalar(
            select(func.coalesce(func.sum(MemorialInvoice.balance), 0)).where(
                MemorialInvoice.organization_id == org_id,
                MemorialInvoice.status.in_(["pending", "partial", "overdue"]),
            )
        ) or 0

        overdue = await db.scalar(
            select(func.count(MemorialInvoice.id)).where(
                MemorialInvoice.organization_id == org_id,
                MemorialInvoice.status.in_(["pending", "partial", "overdue"]),
                MemorialInvoice.due_date < today,
            )
        ) or 0

        return [
            DashboardMetric(
                key="memorial.services_open",
                label="Servicios abiertos",
                value=_fmt_int(int(services_open)),
                raw_value=float(services_open),
                icon="briefcase",
                color="#0F766E",
                app_code="memorial",
            ),
            DashboardMetric(
                key="memorial.contracts_active",
                label="Contratos activos",
                value=_fmt_int(int(contracts_active)),
                raw_value=float(contracts_active),
                icon="file-text",
                color="#0EA5E9",
                app_code="memorial",
            ),
            DashboardMetric(
                key="memorial.income_month",
                label="Ingresos del mes",
                value=_fmt_money(income),
                raw_value=float(income),
                icon="trending-up",
                color="#059669",
                app_code="memorial",
            ),
            DashboardMetric(
                key="memorial.receivables",
                label="Cartera por cobrar",
                value=_fmt_money(receivables),
                raw_value=float(receivables),
                icon="alert-circle",
                color="#D97706",
                app_code="memorial",
            ),
            DashboardMetric(
                key="memorial.overdue.alert",
                label="Facturas vencidas",
                value=_fmt_int(int(overdue)),
                raw_value=float(overdue),
                icon="alert-triangle",
                color="#DC2626",
                app_code="memorial",
            ),
        ]

    # ------------------------------------------------------------------
    # Water KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _water_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from src.apps.water.models import WaterInvoice, WaterPayment, WaterSubscriber
        today = date.today()
        first_of_month = today.replace(day=1)

        subscribers = await db.scalar(
            select(func.count(WaterSubscriber.id)).where(
                WaterSubscriber.organization_id == org_id,
                WaterSubscriber.status == "active",
            )
        ) or 0

        income = await db.scalar(
            select(func.coalesce(func.sum(WaterPayment.amount), 0)).where(
                WaterPayment.organization_id == org_id,
                WaterPayment.payment_date >= first_of_month,
                WaterPayment.payment_date <= today,
            )
        ) or 0

        receivables = await db.scalar(
            select(func.coalesce(func.sum(WaterInvoice.balance), 0)).where(
                WaterInvoice.organization_id == org_id,
                WaterInvoice.status.in_(["pending", "partial", "overdue"]),
            )
        ) or 0

        overdue = await db.scalar(
            select(func.count(WaterInvoice.id)).where(
                WaterInvoice.organization_id == org_id,
                WaterInvoice.status.in_(["pending", "partial", "overdue"]),
                WaterInvoice.due_date < today,
            )
        ) or 0

        return [
            DashboardMetric(
                key="water.subscribers",
                label="Suscriptores activos",
                value=_fmt_int(int(subscribers)),
                raw_value=float(subscribers),
                icon="droplet",
                color="#0284C7",
                app_code="water",
            ),
            DashboardMetric(
                key="water.income_month",
                label="Ingresos del mes",
                value=_fmt_money(income),
                raw_value=float(income),
                icon="trending-up",
                color="#059669",
                app_code="water",
            ),
            DashboardMetric(
                key="water.receivables",
                label="Cartera por cobrar",
                value=_fmt_money(receivables),
                raw_value=float(receivables),
                icon="alert-circle",
                color="#D97706",
                app_code="water",
            ),
            DashboardMetric(
                key="water.overdue.alert",
                label="Facturas vencidas",
                value=_fmt_int(int(overdue)),
                raw_value=float(overdue),
                icon="alert-triangle",
                color="#DC2626",
                app_code="water",
            ),
        ]

    # ------------------------------------------------------------------
    # POS KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _pos_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from datetime import datetime, time as dtime, timezone
        from src.apps.pos.sales.models import PosSale
        today = date.today()
        first_of_month = today.replace(day=1)
        # Use created_at (DateTime); compare against UTC midnight of first_of_month
        month_start = datetime.combine(first_of_month, dtime.min, tzinfo=timezone.utc)

        income = await db.scalar(
            select(func.coalesce(func.sum(PosSale.total), 0)).where(
                PosSale.organization_id == org_id,
                PosSale.status == "completed",
                PosSale.created_at >= month_start,
            )
        ) or 0

        count = await db.scalar(
            select(func.count(PosSale.id)).where(
                PosSale.organization_id == org_id,
                PosSale.status == "completed",
                PosSale.created_at >= month_start,
            )
        ) or 0

        return [
            DashboardMetric(
                key="pos.sales_month_count",
                label="Ventas del mes",
                value=_fmt_int(int(count)),
                raw_value=float(count),
                icon="shopping-cart",
                color="#9333EA",
                app_code="pos",
            ),
            DashboardMetric(
                key="pos.income_month",
                label="Ingresos del mes",
                value=_fmt_money(income),
                raw_value=float(income),
                icon="trending-up",
                color="#059669",
                app_code="pos",
            ),
        ]

    # ------------------------------------------------------------------
    # Parking KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _parking_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from datetime import datetime, time as dtime, timezone
        from src.apps.parking.sessions.models import ParkingSession
        today = date.today()
        first_of_month = today.replace(day=1)
        month_start = datetime.combine(first_of_month, dtime.min, tzinfo=timezone.utc)
        day_start = datetime.combine(today, dtime.min, tzinfo=timezone.utc)

        active = await db.scalar(
            select(func.count(ParkingSession.id)).where(
                ParkingSession.organization_id == org_id,
                ParkingSession.status == "active",
            )
        ) or 0

        sessions_today = await db.scalar(
            select(func.count(ParkingSession.id)).where(
                ParkingSession.organization_id == org_id,
                ParkingSession.entry_time >= day_start,
            )
        ) or 0

        income = await db.scalar(
            select(func.coalesce(func.sum(ParkingSession.total), 0)).where(
                ParkingSession.organization_id == org_id,
                ParkingSession.payment_status == "paid",
                ParkingSession.entry_time >= month_start,
            )
        ) or 0

        return [
            DashboardMetric(
                key="parking.active_sessions",
                label="Sesiones activas",
                value=_fmt_int(int(active)),
                raw_value=float(active),
                icon="car",
                color="#0EA5E9",
                app_code="parking",
            ),
            DashboardMetric(
                key="parking.sessions_today",
                label="Ingresos hoy",
                value=_fmt_int(int(sessions_today)),
                raw_value=float(sessions_today),
                icon="clock",
                color="#6366F1",
                app_code="parking",
            ),
            DashboardMetric(
                key="parking.income_month",
                label="Ingresos del mes",
                value=_fmt_money(income),
                raw_value=float(income),
                icon="trending-up",
                color="#059669",
                app_code="parking",
            ),
        ]

    # ------------------------------------------------------------------
    # Health KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _health_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from src.apps.health.patients.models import HealthPatient
        from src.apps.health.appointments.models import HealthAppointment
        today = date.today()
        first_of_month = today.replace(day=1)

        active_patients = await db.scalar(
            select(func.count(HealthPatient.id)).where(
                HealthPatient.organization_id == org_id,
                HealthPatient.status == "active",
            )
        ) or 0

        appts_today = await db.scalar(
            select(func.count(HealthAppointment.id)).where(
                HealthAppointment.organization_id == org_id,
                HealthAppointment.appointment_date == today,
                HealthAppointment.status.in_(["scheduled", "confirmed", "in_progress"]),
            )
        ) or 0

        income = await db.scalar(
            select(func.coalesce(func.sum(HealthAppointment.amount), 0)).where(
                HealthAppointment.organization_id == org_id,
                HealthAppointment.payment_status == "paid",
                HealthAppointment.appointment_date >= first_of_month,
                HealthAppointment.appointment_date <= today,
            )
        ) or 0

        return [
            DashboardMetric(
                key="health.active_patients",
                label="Pacientes activos",
                value=_fmt_int(int(active_patients)),
                raw_value=float(active_patients),
                icon="heart",
                color="#DC2626",
                app_code="health",
            ),
            DashboardMetric(
                key="health.appointments_today",
                label="Citas hoy",
                value=_fmt_int(int(appts_today)),
                raw_value=float(appts_today),
                icon="calendar",
                color="#0EA5E9",
                app_code="health",
            ),
            DashboardMetric(
                key="health.income_month",
                label="Ingresos del mes",
                value=_fmt_money(income),
                raw_value=float(income),
                icon="trending-up",
                color="#059669",
                app_code="health",
            ),
        ]

    # ------------------------------------------------------------------
    # Pay KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _pay_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from datetime import datetime, time as dtime, timezone
        from src.apps.pay.transactions.models import PayTransaction
        today = date.today()
        first_of_month = today.replace(day=1)
        month_start = datetime.combine(first_of_month, dtime.min, tzinfo=timezone.utc)

        tx_count = await db.scalar(
            select(func.count(PayTransaction.id)).where(
                PayTransaction.organization_id == org_id,
                PayTransaction.status.in_(["captured", "settled"]),
                PayTransaction.created_at >= month_start,
            )
        ) or 0

        volume = await db.scalar(
            select(func.coalesce(func.sum(PayTransaction.net_amount), 0)).where(
                PayTransaction.organization_id == org_id,
                PayTransaction.status.in_(["captured", "settled"]),
                PayTransaction.created_at >= month_start,
            )
        ) or 0

        failed = await db.scalar(
            select(func.count(PayTransaction.id)).where(
                PayTransaction.organization_id == org_id,
                PayTransaction.status == "failed",
                PayTransaction.created_at >= month_start,
            )
        ) or 0

        return [
            DashboardMetric(
                key="pay.transactions_month",
                label="Transacciones del mes",
                value=_fmt_int(int(tx_count)),
                raw_value=float(tx_count),
                icon="credit-card",
                color="#9333EA",
                app_code="pay",
            ),
            DashboardMetric(
                key="pay.income_month",
                label="Volumen del mes",
                value=_fmt_money(volume),
                raw_value=float(volume),
                icon="trending-up",
                color="#059669",
                app_code="pay",
            ),
            DashboardMetric(
                key="pay.failed.alert",
                label="Transacciones fallidas",
                value=_fmt_int(int(failed)),
                raw_value=float(failed),
                icon="alert-triangle",
                color="#DC2626",
                app_code="pay",
            ),
        ]

    # ------------------------------------------------------------------
    # Condo KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _condo_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from src.apps.condo.fees.models import CondoFee
        today = date.today()
        first_of_month = today.replace(day=1)
        period_now = today.strftime("%Y-%m")

        # Cuotas pagadas del mes (sum paid_amount)
        income = await db.scalar(
            select(func.coalesce(func.sum(CondoFee.paid_amount), 0)).where(
                CondoFee.organization_id == org_id,
                CondoFee.paid_date >= first_of_month,
                CondoFee.paid_date <= today,
            )
        ) or 0

        # Cartera (saldo = total - paid_amount) sobre cuotas no pagadas
        receivables = await db.scalar(
            select(func.coalesce(func.sum(CondoFee.total - CondoFee.paid_amount), 0)).where(
                CondoFee.organization_id == org_id,
                CondoFee.status.in_(["pending", "partial", "overdue"]),
            )
        ) or 0

        # Cuotas vencidas
        overdue = await db.scalar(
            select(func.count(CondoFee.id)).where(
                CondoFee.organization_id == org_id,
                CondoFee.status.in_(["pending", "partial", "overdue"]),
                CondoFee.due_date < today,
            )
        ) or 0

        return [
            DashboardMetric(
                key="condo.income_month",
                label="Cuotas recaudadas mes",
                value=_fmt_money(income),
                raw_value=float(income),
                icon="trending-up",
                color="#059669",
                app_code="condo",
            ),
            DashboardMetric(
                key="condo.receivables",
                label="Cartera por cobrar",
                value=_fmt_money(receivables),
                raw_value=float(receivables),
                icon="alert-circle",
                color="#D97706",
                app_code="condo",
            ),
            DashboardMetric(
                key="condo.overdue.alert",
                label="Cuotas vencidas",
                value=_fmt_int(int(overdue)),
                raw_value=float(overdue),
                icon="alert-triangle",
                color="#DC2626",
                app_code="condo",
            ),
        ]

    # ------------------------------------------------------------------
    # Credit KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _credit_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from src.apps.credit.loans.models import CreditLoan
        from src.apps.credit.payments.models import CreditPayment

        today = date.today()
        first_of_month = today.replace(day=1)

        active_loans = await db.scalar(
            select(func.count(CreditLoan.id)).where(
                CreditLoan.organization_id == org_id,
                CreditLoan.status.in_(["active", "current", "delinquent"]),
            )
        ) or 0

        # Cartera viva = suma de balance_principal de préstamos activos
        portfolio = await db.scalar(
            select(func.coalesce(func.sum(CreditLoan.balance_principal), 0)).where(
                CreditLoan.organization_id == org_id,
                CreditLoan.status.in_(["active", "current", "delinquent"]),
            )
        ) or 0

        delinquent = await db.scalar(
            select(func.count(CreditLoan.id)).where(
                CreditLoan.organization_id == org_id,
                CreditLoan.status == "delinquent",
            )
        ) or 0

        # Ingresos del mes = suma de pagos
        income = await db.scalar(
            select(func.coalesce(func.sum(CreditPayment.amount), 0)).where(
                CreditPayment.organization_id == org_id,
                CreditPayment.payment_date >= first_of_month,
                CreditPayment.payment_date <= today,
            )
        ) or 0

        return [
            DashboardMetric(
                key="credit.active_loans",
                label="Préstamos activos",
                value=_fmt_int(int(active_loans)),
                raw_value=float(active_loans),
                icon="dollar-sign",
                color="#0EA5E9",
                app_code="credit",
            ),
            DashboardMetric(
                key="credit.portfolio",
                label="Cartera viva",
                value=_fmt_money(portfolio),
                raw_value=float(portfolio),
                icon="briefcase",
                color="#7C3AED",
                app_code="credit",
            ),
            DashboardMetric(
                key="credit.income_month",
                label="Recaudo del mes",
                value=_fmt_money(income),
                raw_value=float(income),
                icon="trending-up",
                color="#059669",
                app_code="credit",
            ),
            DashboardMetric(
                key="credit.delinquent.alert",
                label="Préstamos en mora",
                value=_fmt_int(int(delinquent)),
                raw_value=float(delinquent),
                icon="alert-triangle",
                color="#DC2626",
                app_code="credit",
            ),
        ]

    # ------------------------------------------------------------------
    # Edu KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _edu_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from src.apps.edu.students.models import EduStudent
        from src.apps.edu.finance.models import EduStudentCharge

        today = date.today()

        active_students = await db.scalar(
            select(func.count(EduStudent.id)).where(
                EduStudent.organization_id == org_id,
                EduStudent.academic_status == "active",
            )
        ) or 0

        receivables = await db.scalar(
            select(func.coalesce(func.sum(EduStudentCharge.balance), 0)).where(
                EduStudentCharge.organization_id == org_id,
                EduStudentCharge.status.in_(["pending", "overdue"]),
            )
        ) or 0

        overdue = await db.scalar(
            select(func.count(EduStudentCharge.id)).where(
                EduStudentCharge.organization_id == org_id,
                EduStudentCharge.status.in_(["pending", "overdue"]),
                EduStudentCharge.due_date.is_not(None),
                EduStudentCharge.due_date < today,
            )
        ) or 0

        return [
            DashboardMetric(
                key="edu.active_students",
                label="Estudiantes activos",
                value=_fmt_int(int(active_students)),
                raw_value=float(active_students),
                icon="users",
                color="#0EA5E9",
                app_code="edu",
            ),
            DashboardMetric(
                key="edu.receivables",
                label="Cartera estudiantil",
                value=_fmt_money(receivables),
                raw_value=float(receivables),
                icon="alert-circle",
                color="#D97706",
                app_code="edu",
            ),
            DashboardMetric(
                key="edu.overdue.alert",
                label="Cobros vencidos",
                value=_fmt_int(int(overdue)),
                raw_value=float(overdue),
                icon="alert-triangle",
                color="#DC2626",
                app_code="edu",
            ),
        ]

    # ------------------------------------------------------------------
    # Family KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _family_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from src.apps.family.models import FamilyMember, FamilyUnit

        units = await db.scalar(
            select(func.count(FamilyUnit.id)).where(
                FamilyUnit.organization_id == org_id,
                FamilyUnit.status == "active",
            )
        ) or 0

        members = await db.scalar(
            select(func.count(FamilyMember.id)).where(
                FamilyMember.organization_id == org_id,
            )
        ) or 0

        return [
            DashboardMetric(
                key="family.units",
                label="Núcleos familiares",
                value=_fmt_int(int(units)),
                raw_value=float(units),
                icon="home",
                color="#7C3AED",
                app_code="family",
            ),
            DashboardMetric(
                key="family.members",
                label="Personas vinculadas",
                value=_fmt_int(int(members)),
                raw_value=float(members),
                icon="users",
                color="#0EA5E9",
                app_code="family",
            ),
        ]

    # ------------------------------------------------------------------
    # CRM KPIs
    # ------------------------------------------------------------------
    @staticmethod
    async def _crm_metrics(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[DashboardMetric]:
        from src.apps.crm.deals.models import CrmDeal
        from src.apps.crm.leads.models import CrmLead

        today = date.today()
        first_of_month = today.replace(day=1)

        leads_open = await db.scalar(
            select(func.count(CrmLead.id)).where(
                CrmLead.organization_id == org_id,
                CrmLead.status.in_(["new", "contacted", "qualified"]),
            )
        ) or 0

        deals_open = await db.scalar(
            select(func.count(CrmDeal.id)).where(
                CrmDeal.organization_id == org_id,
                CrmDeal.status == "open",
            )
        ) or 0

        pipeline_value = await db.scalar(
            select(func.coalesce(func.sum(CrmDeal.value), 0)).where(
                CrmDeal.organization_id == org_id,
                CrmDeal.status == "open",
            )
        ) or 0

        won_month = await db.scalar(
            select(func.coalesce(func.sum(CrmDeal.value), 0)).where(
                CrmDeal.organization_id == org_id,
                CrmDeal.status == "won",
                CrmDeal.won_date >= first_of_month,
                CrmDeal.won_date <= today,
            )
        ) or 0

        return [
            DashboardMetric(
                key="crm.leads_open",
                label="Leads abiertos",
                value=_fmt_int(int(leads_open)),
                raw_value=float(leads_open),
                icon="user-plus",
                color="#0EA5E9",
                app_code="crm",
            ),
            DashboardMetric(
                key="crm.deals_open",
                label="Negocios abiertos",
                value=_fmt_int(int(deals_open)),
                raw_value=float(deals_open),
                icon="target",
                color="#7C3AED",
                app_code="crm",
            ),
            DashboardMetric(
                key="crm.pipeline_value",
                label="Pipeline",
                value=_fmt_money(pipeline_value),
                raw_value=float(pipeline_value),
                icon="briefcase",
                color="#6366F1",
                app_code="crm",
            ),
            DashboardMetric(
                key="crm.income_month",
                label="Cerrado del mes",
                value=_fmt_money(won_month),
                raw_value=float(won_month),
                icon="trending-up",
                color="#059669",
                app_code="crm",
            ),
        ]


dashboard_service = DashboardService()
