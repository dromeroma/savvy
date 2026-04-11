"""Business logic for parking pricing."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.parking.pricing.models import ParkingPricingRule, ParkingSubscription
from src.apps.parking.pricing.schemas import PricingRuleCreate, SubscriptionCreate


class PricingService:

    @staticmethod
    async def list_rules(db: AsyncSession, org_id: uuid.UUID) -> list[ParkingPricingRule]:
        return list((await db.execute(select(ParkingPricingRule).where(ParkingPricingRule.organization_id == org_id).order_by(ParkingPricingRule.name))).scalars().all())

    @staticmethod
    async def create_rule(db: AsyncSession, org_id: uuid.UUID, data: PricingRuleCreate) -> ParkingPricingRule:
        rule = ParkingPricingRule(organization_id=org_id, **data.model_dump())
        db.add(rule)
        await db.flush()
        await db.refresh(rule)
        return rule

    @staticmethod
    async def list_subscriptions(db: AsyncSession, org_id: uuid.UUID) -> list[ParkingSubscription]:
        return list((await db.execute(select(ParkingSubscription).where(ParkingSubscription.organization_id == org_id).order_by(ParkingSubscription.name))).scalars().all())

    @staticmethod
    async def create_subscription(db: AsyncSession, org_id: uuid.UUID, data: SubscriptionCreate) -> ParkingSubscription:
        sub = ParkingSubscription(organization_id=org_id, **data.model_dump())
        db.add(sub)
        await db.flush()
        await db.refresh(sub)
        return sub
