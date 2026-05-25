"""Analytics service — pre-aggregated metrics for the executive dashboard."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.analytics.schemas import (
    AnalyticsResponse,
    MonthlyPoint,
    NeighborhoodStat,
    StratumStat,
    TopDebtor,
)
from src.apps.water.models import (
    WaterConsumption,
    WaterInvoice,
    WaterPayment,
    WaterSubscriber,
)


def _month_buckets(months: int = 12) -> list[date]:
    """Return the first-of-month for the last `months` months, oldest first."""
    today = date.today().replace(day=1)
    out: list[date] = []
    for i in range(months - 1, -1, -1):
        y = today.year
        m = today.month - i
        while m <= 0:
            m += 12
            y -= 1
        out.append(date(y, m, 1))
    return out


def _fill_series(buckets: list[date], by_month: dict[date, tuple[Decimal, int]]) -> list[MonthlyPoint]:
    return [
        MonthlyPoint(
            month=b.strftime("%Y-%m"),
            amount=by_month.get(b, (Decimal("0"), 0))[0],
            count=by_month.get(b, (Decimal("0"), 0))[1],
        )
        for b in buckets
    ]


class AnalyticsService:

    @staticmethod
    async def overview(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> AnalyticsResponse:
        buckets = _month_buckets(12)
        start = buckets[0]
        today = date.today()
        first_of_month = today.replace(day=1)

        # ---- Billed per month ----
        billed_rows = await db.execute(
            select(
                func.date_trunc("month", WaterInvoice.issue_date).label("m"),
                func.coalesce(func.sum(WaterInvoice.total), 0),
                func.count(WaterInvoice.id),
            )
            .where(
                WaterInvoice.organization_id == org_id,
                WaterInvoice.status != "annulled",
                WaterInvoice.issue_date >= start,
            )
            .group_by("m")
        )
        billed_by = {
            r[0].date(): (Decimal(str(r[1])), int(r[2]))
            for r in billed_rows.all() if r[0]
        }

        # ---- Collected per month ----
        collected_rows = await db.execute(
            select(
                func.date_trunc("month", WaterPayment.payment_date).label("m"),
                func.coalesce(func.sum(WaterPayment.amount), 0),
                func.count(WaterPayment.id),
            )
            .where(
                WaterPayment.organization_id == org_id,
                WaterPayment.payment_date >= start,
            )
            .group_by("m")
        )
        collected_by = {
            r[0].date(): (Decimal(str(r[1])), int(r[2]))
            for r in collected_rows.all() if r[0]
        }

        # ---- Consumption per month (m³) ----
        cons_rows = await db.execute(
            select(
                func.date_trunc("month", WaterConsumption.reading_date).label("m"),
                func.coalesce(func.sum(WaterConsumption.consumption_cubic), 0),
                func.count(WaterConsumption.id),
            )
            .where(
                WaterConsumption.organization_id == org_id,
                WaterConsumption.reading_date >= start,
            )
            .group_by("m")
        )
        cons_by = {
            r[0].date(): (Decimal(str(r[1])), int(r[2]))
            for r in cons_rows.all() if r[0]
        }

        # ---- By stratum ----
        stratum_rows = await db.execute(
            select(
                WaterSubscriber.stratum,
                func.count(func.distinct(WaterSubscriber.id)),
                func.coalesce(func.avg(WaterConsumption.consumption_cubic), 0),
                func.coalesce(func.sum(WaterInvoice.total).filter(
                    WaterInvoice.status != "annulled",
                ), 0),
            )
            .outerjoin(WaterConsumption, WaterConsumption.subscriber_id == WaterSubscriber.id)
            .outerjoin(WaterInvoice, WaterInvoice.subscriber_id == WaterSubscriber.id)
            .where(WaterSubscriber.organization_id == org_id)
            .group_by(WaterSubscriber.stratum)
            .order_by(WaterSubscriber.stratum)
        )
        by_stratum = [
            StratumStat(
                stratum=r[0],
                subscribers=int(r[1]),
                avg_consumption_cubic=Decimal(str(r[2])),
                total_billed=Decimal(str(r[3])),
            )
            for r in stratum_rows.all()
        ]

        # ---- By neighborhood (top 10 by open balance) ----
        neigh_rows = await db.execute(
            select(
                WaterSubscriber.neighborhood,
                func.count(func.distinct(WaterSubscriber.id)),
                func.coalesce(func.sum(WaterInvoice.balance).filter(
                    WaterInvoice.status.in_(("pending", "partial", "overdue")),
                ), 0),
            )
            .outerjoin(WaterInvoice, WaterInvoice.subscriber_id == WaterSubscriber.id)
            .where(WaterSubscriber.organization_id == org_id)
            .group_by(WaterSubscriber.neighborhood)
            .order_by(func.coalesce(func.sum(WaterInvoice.balance).filter(
                WaterInvoice.status.in_(("pending", "partial", "overdue")),
            ), 0).desc())
            .limit(10)
        )
        by_neigh = [
            NeighborhoodStat(
                neighborhood=r[0],
                subscribers=int(r[1]),
                open_balance=Decimal(str(r[2])),
            )
            for r in neigh_rows.all()
        ]

        # ---- Top 10 debtors ----
        top_rows = await db.execute(
            select(
                WaterSubscriber.id, WaterSubscriber.code,
                func.coalesce(
                    WaterSubscriber.business_name,
                    func.concat(
                        WaterSubscriber.first_name, " ",
                        func.coalesce(WaterSubscriber.last_name, ""),
                    ),
                ).label("name"),
                func.min(WaterInvoice.due_date).label("oldest"),
                func.coalesce(func.sum(WaterInvoice.balance), 0).label("bal"),
            )
            .join(WaterInvoice, WaterInvoice.subscriber_id == WaterSubscriber.id)
            .where(
                WaterSubscriber.organization_id == org_id,
                WaterInvoice.status.in_(("overdue", "partial")),
                WaterInvoice.balance > 0,
            )
            .group_by(
                WaterSubscriber.id, WaterSubscriber.code,
                WaterSubscriber.business_name, WaterSubscriber.first_name,
                WaterSubscriber.last_name,
            )
            .order_by(func.coalesce(func.sum(WaterInvoice.balance), 0).desc())
            .limit(10)
        )
        today_d = date.today()
        top_debtors = []
        for r in top_rows.all():
            oldest = r[3]
            days = (today_d - oldest).days if oldest else 0
            top_debtors.append(TopDebtor(
                subscriber_id=str(r[0]), code=r[1],
                name=(r[2].strip() if r[2] else ""),
                days_overdue=max(0, days),
                balance=Decimal(str(r[4])),
            ))

        # ---- Misc KPIs ----
        new_subs = await db.scalar(
            select(func.count(WaterSubscriber.id)).where(
                WaterSubscriber.organization_id == org_id,
                func.date(WaterSubscriber.created_at) >= today - timedelta(days=30),
            )
        ) or 0

        avg_collection = Decimal("0")
        if collected_by:
            total_collected_12m = sum((v[0] for v in collected_by.values()), Decimal("0"))
            avg_collection = (total_collected_12m / Decimal("365")).quantize(Decimal("0.01"))

        # Collection rate this month
        billed_month = await db.scalar(
            select(func.coalesce(func.sum(WaterInvoice.total), 0)).where(
                WaterInvoice.organization_id == org_id,
                WaterInvoice.status != "annulled",
                WaterInvoice.issue_date >= first_of_month,
            )
        ) or 0
        paid_month = await db.scalar(
            select(func.coalesce(func.sum(WaterPayment.amount), 0)).where(
                WaterPayment.organization_id == org_id,
                WaterPayment.payment_date >= first_of_month,
            )
        ) or 0
        rate = Decimal("0")
        if Decimal(str(billed_month)) > 0:
            rate = (Decimal(str(paid_month)) / Decimal(str(billed_month))).quantize(Decimal("0.0001"))

        return AnalyticsResponse(
            billed_trend=_fill_series(buckets, billed_by),
            collected_trend=_fill_series(buckets, collected_by),
            consumption_trend=_fill_series(buckets, cons_by),
            by_stratum=by_stratum,
            by_neighborhood=by_neigh,
            top_debtors=top_debtors,
            new_subscribers_last_30d=int(new_subs),
            avg_collection_per_day=avg_collection,
            collection_rate=rate,
        )
