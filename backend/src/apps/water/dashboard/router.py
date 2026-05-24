"""Water dashboard endpoint — KPIs for the org."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.cash_accounts.service import CashAccountsService
from src.apps.water.models import WaterInvoice, WaterMeter, WaterPayment, WaterSubscriber
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(
    prefix="/dashboard",
    tags=["Water · Dashboard"],
    dependencies=[Depends(require_permission("water", "dashboard.view", "subscribers.read"))],
)


def _f(n) -> float:
    return float(n or 0)


@router.get("/kpis")
async def get_kpis(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    today = date.today()
    first_of_month = today.replace(day=1)

    # Subscribers by status
    by_status = dict((await db.execute(
        select(WaterSubscriber.status, func.count(WaterSubscriber.id))
        .where(WaterSubscriber.organization_id == org_id)
        .group_by(WaterSubscriber.status)
    )).all())
    total_subscribers = sum(by_status.values()) if by_status else 0

    # Meters
    total_meters = await db.scalar(
        select(func.count(WaterMeter.id)).where(WaterMeter.organization_id == org_id),
    ) or 0
    assigned_meters = await db.scalar(
        select(func.count(WaterMeter.id)).where(
            WaterMeter.organization_id == org_id,
            WaterMeter.subscriber_id.isnot(None),
        ),
    ) or 0

    # Invoices this month
    invoices_this_month = await db.scalar(
        select(func.count(WaterInvoice.id))
        .where(
            WaterInvoice.organization_id == org_id,
            WaterInvoice.issue_date >= first_of_month,
            WaterInvoice.status != "annulled",
        )
    ) or 0

    # Billed this month (sum of totals)
    billed_this_month = await db.scalar(
        select(func.coalesce(func.sum(WaterInvoice.total), 0))
        .where(
            WaterInvoice.organization_id == org_id,
            WaterInvoice.issue_date >= first_of_month,
            WaterInvoice.status != "annulled",
        )
    ) or 0

    # Pending balance (open cartera)
    pending_balance = await db.scalar(
        select(func.coalesce(func.sum(WaterInvoice.balance), 0))
        .where(
            WaterInvoice.organization_id == org_id,
            WaterInvoice.status.in_(("pending", "partial", "overdue")),
        )
    ) or 0

    # Payments this month
    paid_this_month = await db.scalar(
        select(func.coalesce(func.sum(WaterPayment.amount), 0))
        .where(
            WaterPayment.organization_id == org_id,
            WaterPayment.payment_date >= first_of_month,
        )
    ) or 0

    # Today's collections
    paid_today = await db.scalar(
        select(func.coalesce(func.sum(WaterPayment.amount), 0))
        .where(
            WaterPayment.organization_id == org_id,
            WaterPayment.payment_date == today,
        )
    ) or 0

    # Overdue cartera (past-due unpaid)
    overdue_invoices = await db.scalar(
        select(func.count(WaterInvoice.id))
        .where(
            WaterInvoice.organization_id == org_id,
            WaterInvoice.status == "overdue",
            WaterInvoice.balance > 0,
        )
    ) or 0
    overdue_balance = await db.scalar(
        select(func.coalesce(func.sum(WaterInvoice.balance), 0))
        .where(
            WaterInvoice.organization_id == org_id,
            WaterInvoice.status == "overdue",
            WaterInvoice.balance > 0,
        )
    ) or 0
    overdue_subscribers = await db.scalar(
        select(func.count(func.distinct(WaterInvoice.subscriber_id)))
        .where(
            WaterInvoice.organization_id == org_id,
            WaterInvoice.status == "overdue",
            WaterInvoice.balance > 0,
        )
    ) or 0

    # Treasury — total cash on hand across all accounts
    accounts = await CashAccountsService.list_accounts(db, org_id, active_only=False)
    cash_total = sum((Decimal(a.current_balance) for a in accounts), start=Decimal("0"))
    cash_accounts_count = len(accounts)

    return {
        "total_subscribers": int(total_subscribers),
        "by_status": {
            "active": int(by_status.get("active", 0)),
            "suspended": int(by_status.get("suspended", 0)),
            "overdue": int(by_status.get("overdue", 0)),
            "retired": int(by_status.get("retired", 0)),
        },
        "total_meters": int(total_meters),
        "assigned_meters": int(assigned_meters),
        "unassigned_meters": int(total_meters) - int(assigned_meters),
        "invoices_this_month": int(invoices_this_month),
        "billed_this_month": _f(billed_this_month),
        "pending_balance": _f(pending_balance),
        "paid_this_month": _f(paid_this_month),
        "paid_today": _f(paid_today),
        "overdue_invoices": int(overdue_invoices),
        "overdue_balance": _f(overdue_balance),
        "overdue_subscribers": int(overdue_subscribers),
        "cash_on_hand": _f(cash_total),
        "cash_accounts_count": int(cash_accounts_count),
    }
