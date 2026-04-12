"""Business logic for condo fees — generation and payment."""

from __future__ import annotations
import uuid
from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.condo.fees.models import CondoFee
from src.apps.condo.fees.schemas import FeeGenerate
from src.apps.condo.properties.models import CondoProperty, CondoUnit


class FeeService:
    @staticmethod
    async def generate_fees(db: AsyncSession, org_id: uuid.UUID, data: FeeGenerate) -> list[CondoFee]:
        """Generate monthly fees for all units in a property based on coefficients."""
        prop_result = await db.execute(select(CondoProperty).where(CondoProperty.id == data.property_id, CondoProperty.organization_id == org_id))
        prop = prop_result.scalar_one_or_none()
        if prop is None: raise NotFoundError("Property not found.")

        units_result = await db.execute(select(CondoUnit).where(CondoUnit.property_id == data.property_id))
        units = list(units_result.scalars().all())

        base = Decimal(str(prop.admin_fee_base))
        fees = []
        for unit in units:
            coeff = Decimal(str(unit.coefficient))
            amount = (base * coeff).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            fee = CondoFee(
                organization_id=org_id, unit_id=unit.id, period=data.period,
                amount=float(amount), total=float(amount), due_date=data.due_date,
            )
            db.add(fee)
            fees.append(fee)
        await db.flush()
        for f in fees: await db.refresh(f)
        return fees

    @staticmethod
    async def list_fees(db: AsyncSession, org_id: uuid.UUID, unit_id: uuid.UUID | None = None, period: str | None = None, status_filter: str | None = None) -> list[CondoFee]:
        q = select(CondoFee).where(CondoFee.organization_id == org_id)
        if unit_id: q = q.where(CondoFee.unit_id == unit_id)
        if period: q = q.where(CondoFee.period == period)
        if status_filter: q = q.where(CondoFee.status == status_filter)
        return list((await db.execute(q.order_by(CondoFee.due_date.desc()))).scalars().all())

    @staticmethod
    async def pay_fee(db: AsyncSession, org_id: uuid.UUID, fee_id: uuid.UUID, amount: float) -> CondoFee:
        result = await db.execute(select(CondoFee).where(CondoFee.id == fee_id, CondoFee.organization_id == org_id))
        fee = result.scalar_one_or_none()
        if fee is None: raise NotFoundError("Fee not found.")
        fee.paid_amount = float(Decimal(str(fee.paid_amount)) + Decimal(str(amount)))
        fee.paid_date = date.today()
        fee.status = "paid" if Decimal(str(fee.paid_amount)) >= Decimal(str(fee.total)) else "partial"
        await db.flush(); await db.refresh(fee); return fee
