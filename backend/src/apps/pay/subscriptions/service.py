"""Business logic for SavvyPay subscriptions."""

from __future__ import annotations
import uuid
from datetime import date, timedelta
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.pay.subscriptions.models import PaySubscription, PaySubscriptionPlan
from src.apps.pay.subscriptions.schemas import PlanCreate, SubscriptionCreate
from src.apps.pay.ledger.service import LedgerEngine


class SubscriptionService:

    @staticmethod
    async def list_plans(db: AsyncSession, org_id: uuid.UUID) -> list[PaySubscriptionPlan]:
        return list((await db.execute(select(PaySubscriptionPlan).where(PaySubscriptionPlan.organization_id == org_id).order_by(PaySubscriptionPlan.name))).scalars().all())

    @staticmethod
    async def create_plan(db: AsyncSession, org_id: uuid.UUID, data: PlanCreate) -> PaySubscriptionPlan:
        p = PaySubscriptionPlan(organization_id=org_id, **data.model_dump())
        db.add(p); await db.flush(); await db.refresh(p); return p

    @staticmethod
    async def subscribe(db: AsyncSession, org_id: uuid.UUID, data: SubscriptionCreate) -> PaySubscription:
        plan_result = await db.execute(select(PaySubscriptionPlan).where(PaySubscriptionPlan.id == data.plan_id))
        plan = plan_result.scalar_one_or_none()
        today = date.today()

        cycle_days = {"weekly": 7, "monthly": 30, "quarterly": 90, "annual": 365}
        period_end = today + timedelta(days=cycle_days.get(plan.billing_cycle, 30) if plan else 30)

        sub = PaySubscription(
            organization_id=org_id, plan_id=data.plan_id, wallet_id=data.wallet_id,
            current_period_start=today, current_period_end=period_end,
            next_billing_date=period_end,
        )
        db.add(sub)
        await db.flush()
        await db.refresh(sub)

        await LedgerEngine.emit_event(db, org_id, "subscription.created", "subscription", sub.id,
            {"plan_id": str(data.plan_id), "period_end": str(period_end)})
        return sub

    @staticmethod
    async def list_subscriptions(db: AsyncSession, org_id: uuid.UUID) -> list[PaySubscription]:
        return list((await db.execute(select(PaySubscription).where(PaySubscription.organization_id == org_id).order_by(PaySubscription.created_at.desc()))).scalars().all())
