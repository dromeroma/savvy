"""Business logic for SavvyPay fees."""

from __future__ import annotations
import uuid
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.pay.fees.models import PayFeeRule
from src.apps.pay.fees.schemas import FeeRuleCreate


class FeeService:

    @staticmethod
    async def list_rules(db: AsyncSession, org_id: uuid.UUID) -> list[PayFeeRule]:
        return list((await db.execute(select(PayFeeRule).where(PayFeeRule.organization_id == org_id).order_by(PayFeeRule.name))).scalars().all())

    @staticmethod
    async def create_rule(db: AsyncSession, org_id: uuid.UUID, data: FeeRuleCreate) -> PayFeeRule:
        rule = PayFeeRule(organization_id=org_id, **data.model_dump())
        db.add(rule); await db.flush(); await db.refresh(rule); return rule

    @staticmethod
    async def calculate_fee(db: AsyncSession, org_id: uuid.UUID, amount: float, tx_type: str = "payment", source_app: str | None = None) -> Decimal:
        """Calculate applicable fee for a transaction amount."""
        q = select(PayFeeRule).where(
            PayFeeRule.organization_id == org_id,
            PayFeeRule.is_active == True,
            PayFeeRule.applies_to.in_([tx_type, "all"]),
        )
        if source_app:
            # Try app-specific first, then fallback to generic
            pass
        result = await db.execute(q.order_by(PayFeeRule.created_at).limit(1))
        rule = result.scalar_one_or_none()
        if rule is None:
            return Decimal("0")

        amt = Decimal(str(amount))
        if rule.fee_type == "percentage":
            fee = (amt * Decimal(str(rule.percentage_value)) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        elif rule.fee_type == "fixed":
            fee = Decimal(str(rule.fixed_value))
        else:  # tiered
            fee = Decimal("0")
            # Process tiers from rules JSONB
            for tier in (rule.rules or []):
                if tier.get("up_to") and amt <= Decimal(str(tier["up_to"])):
                    fee = (amt * Decimal(str(tier.get("percentage", 0))) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                    break
            else:
                fee = (amt * Decimal(str(rule.percentage_value)) / 100).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        fee = max(fee, Decimal(str(rule.min_fee)))
        if rule.max_fee:
            fee = min(fee, Decimal(str(rule.max_fee)))
        return fee
