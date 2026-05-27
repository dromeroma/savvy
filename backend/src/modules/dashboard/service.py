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


dashboard_service = DashboardService()
