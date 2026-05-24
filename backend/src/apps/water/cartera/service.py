"""Cartera service — overdue recalculation, aging buckets, debtor list."""

from __future__ import annotations

import math
import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.cartera.schemas import (
    AgingBucket,
    AgingReport,
    OverdueSubscriber,
    RecalcResult,
)
from src.apps.water.models import WaterInvoice, WaterSubscriber
from src.apps.water.tariffs.service import TariffsService


class CarteraService:

    # ------------------------------------------------------------------
    # Recalcular mora
    # ------------------------------------------------------------------
    @staticmethod
    async def recalc_overdue(
        db: AsyncSession,
        org_id: uuid.UUID,
        on_date: date | None = None,
    ) -> RecalcResult:
        """Mark past-due invoices as overdue, apply monthly compound-style
        late interest, and sync subscriber.status accordingly.

        Late interest is computed simple: months_late * rate * base_total
        where base_total = total - late_interest_already_applied. This keeps
        the math idempotent: running the job twice in the same month doesn't
        double-charge interest.
        """
        today = on_date or date.today()
        result = RecalcResult(
            invoices_marked_overdue=0,
            invoices_with_interest_applied=0,
            subscribers_marked_overdue=0,
            subscribers_recovered=0,
            total_interest_applied=Decimal("0"),
        )

        # 1) Recompute per-invoice
        invoices = (
            await db.execute(
                select(WaterInvoice, WaterSubscriber)
                .join(WaterSubscriber, WaterSubscriber.id == WaterInvoice.subscriber_id)
                .where(
                    WaterInvoice.organization_id == org_id,
                    WaterInvoice.status.in_(("pending", "partial", "overdue")),
                    WaterInvoice.due_date < today,
                )
            )
        ).all()
        # cache tariff per (sub_type, stratum)
        tariff_cache: dict[tuple[str, int | None], Decimal] = {}

        for inv, sub in invoices:
            # Mark overdue
            if inv.status != "overdue":
                inv.status = "overdue"
                result.invoices_marked_overdue += 1

            # Determine interest rate from the applicable tariff at issue date
            key = (sub.subscriber_type, sub.stratum)
            if key not in tariff_cache:
                t = await TariffsService.resolve_for_subscriber(
                    db, org_id,
                    subscriber_type=sub.subscriber_type,
                    stratum=sub.stratum,
                    on_date=inv.issue_date,
                )
                tariff_cache[key] = Decimal(t.late_interest_rate) if t else Decimal("0")
            rate = tariff_cache[key]
            if rate <= 0:
                continue

            # Months overdue (ceil so any partial month counts)
            days_overdue = (today - inv.due_date).days
            if days_overdue <= 0:
                continue
            months_overdue = math.ceil(days_overdue / 30)

            # Base is the pre-interest total
            base = Decimal(inv.total) - Decimal(inv.late_interest)
            new_interest = (base * rate * Decimal(months_overdue)).quantize(Decimal("0.01"))
            if new_interest <= Decimal(inv.late_interest):
                continue
            diff = new_interest - Decimal(inv.late_interest)
            inv.late_interest = new_interest
            inv.total = base + new_interest
            inv.balance = Decimal(inv.total) - Decimal(inv.paid_amount)
            result.invoices_with_interest_applied += 1
            result.total_interest_applied += diff

        # 2) Sync subscriber.status
        # Subscribers with at least one overdue invoice (after recalc)
        overdue_sub_ids = set((await db.execute(
            select(WaterInvoice.subscriber_id)
            .where(
                WaterInvoice.organization_id == org_id,
                WaterInvoice.status == "overdue",
            )
            .group_by(WaterInvoice.subscriber_id)
        )).scalars().all())

        subs = (await db.execute(
            select(WaterSubscriber).where(WaterSubscriber.organization_id == org_id)
        )).scalars().all()

        for s in subs:
            should_be_overdue = s.id in overdue_sub_ids
            if should_be_overdue and s.status == "active":
                s.status = "overdue"
                result.subscribers_marked_overdue += 1
            elif not should_be_overdue and s.status == "overdue":
                s.status = "active"
                result.subscribers_recovered += 1

        await db.flush()
        return result

    # ------------------------------------------------------------------
    # Aging report
    # ------------------------------------------------------------------
    @staticmethod
    async def aging_report(
        db: AsyncSession,
        org_id: uuid.UUID,
        on_date: date | None = None,
    ) -> AgingReport:
        today = on_date or date.today()
        days_overdue = func.cast(today - WaterInvoice.due_date, type_=None)
        # Bucket expression: 0_30 | 31_60 | 61_90 | 90_plus | current
        days = func.greatest(0, today - WaterInvoice.due_date)
        bucket = case(
            (days <= 0, "current"),
            (days <= 30, "0_30"),
            (days <= 60, "31_60"),
            (days <= 90, "61_90"),
            else_="90_plus",
        )
        rows = await db.execute(
            select(
                bucket.label("b"),
                func.count(WaterInvoice.id),
                func.coalesce(func.sum(WaterInvoice.balance), 0),
            )
            .where(
                WaterInvoice.organization_id == org_id,
                WaterInvoice.status.in_(("pending", "partial", "overdue")),
                WaterInvoice.balance > 0,
            )
            .group_by("b")
        )
        by_bucket: dict[str, tuple[int, Decimal]] = {}
        for r in rows.all():
            by_bucket[r[0]] = (int(r[1]), Decimal(str(r[2])))

        ordered_keys = ["current", "0_30", "31_60", "61_90", "90_plus"]
        buckets = [
            AgingBucket(
                bucket=k,
                invoices=by_bucket.get(k, (0, Decimal("0")))[0],
                balance=by_bucket.get(k, (0, Decimal("0")))[1],
            )
            for k in ordered_keys
        ]
        total = sum((b.balance for b in buckets), start=Decimal("0"))
        return AgingReport(total_balance=total, buckets=buckets)

    # ------------------------------------------------------------------
    # Overdue subscriber list (priority work queue)
    # ------------------------------------------------------------------
    @staticmethod
    async def overdue_subscribers(
        db: AsyncSession,
        org_id: uuid.UUID,
        limit: int = 100,
        on_date: date | None = None,
    ) -> list[OverdueSubscriber]:
        today = on_date or date.today()
        rows = await db.execute(
            select(
                WaterSubscriber.id,
                WaterSubscriber.code,
                func.coalesce(
                    WaterSubscriber.business_name,
                    func.concat(
                        WaterSubscriber.first_name, " ",
                        func.coalesce(WaterSubscriber.last_name, ""),
                    ),
                ).label("name"),
                WaterSubscriber.phone,
                WaterSubscriber.mobile,
                WaterSubscriber.status,
                func.count(WaterInvoice.id).label("overdue_invoices"),
                func.min(WaterInvoice.due_date).label("oldest"),
                func.coalesce(func.sum(WaterInvoice.balance), 0).label("total"),
            )
            .join(WaterInvoice, WaterInvoice.subscriber_id == WaterSubscriber.id)
            .where(
                WaterSubscriber.organization_id == org_id,
                WaterInvoice.status.in_(("overdue", "partial")),
                WaterInvoice.balance > 0,
                WaterInvoice.due_date < today,
            )
            .group_by(
                WaterSubscriber.id, WaterSubscriber.code, WaterSubscriber.business_name,
                WaterSubscriber.first_name, WaterSubscriber.last_name,
                WaterSubscriber.phone, WaterSubscriber.mobile, WaterSubscriber.status,
            )
            .order_by(func.min(WaterInvoice.due_date))
            .limit(limit)
        )
        out: list[OverdueSubscriber] = []
        for r in rows.all():
            oldest = r[7]
            out.append(OverdueSubscriber(
                subscriber_id=r[0], code=r[1],
                name=(r[2].strip() if r[2] else ""),
                phone=r[3], mobile=r[4], status=r[5],
                overdue_invoices=int(r[6]),
                oldest_due_date=oldest.isoformat() if oldest else None,
                days_overdue=(today - oldest).days if oldest else 0,
                total_balance=Decimal(str(r[8])),
            ))
        return out
