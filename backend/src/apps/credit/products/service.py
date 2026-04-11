"""Business logic for SavvyCredit products."""

from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError
from src.apps.credit.products.models import CreditProduct, CreditProductFee
from src.apps.credit.products.schemas import CreditProductCreate, CreditProductUpdate


class CreditProductService:

    @staticmethod
    async def list_products(
        db: AsyncSession, org_id: uuid.UUID, status_filter: str | None = None,
    ) -> list[CreditProduct]:
        q = select(CreditProduct).where(CreditProduct.organization_id == org_id)
        if status_filter:
            q = q.where(CreditProduct.status == status_filter)
        q = q.order_by(CreditProduct.name)
        result = await db.execute(q)
        return list(result.scalars().all())

    @staticmethod
    async def create_product(
        db: AsyncSession, org_id: uuid.UUID, data: CreditProductCreate,
    ) -> CreditProduct:
        product = CreditProduct(
            organization_id=org_id,
            code=data.code,
            name=data.name,
            description=data.description,
            interest_type=data.interest_type,
            interest_rate=data.interest_rate,
            interest_rate_period=data.interest_rate_period,
            amortization_method=data.amortization_method,
            payment_frequency=data.payment_frequency,
            term_min=data.term_min,
            term_max=data.term_max,
            amount_min=data.amount_min,
            amount_max=data.amount_max,
            grace_period_days=data.grace_period_days,
            late_fee_type=data.late_fee_type,
            late_fee_value=data.late_fee_value,
            payment_allocation=data.payment_allocation,
            origination_fee_type=data.origination_fee_type,
            origination_fee_value=data.origination_fee_value,
            requires_guarantor=data.requires_guarantor,
            max_guarantors=data.max_guarantors,
            settings=data.settings,
        )
        db.add(product)
        await db.flush()

        for fee in data.fees:
            f = CreditProductFee(
                product_id=product.id,
                name=fee.name,
                fee_type=fee.fee_type,
                value=fee.value,
                applies_to=fee.applies_to,
                is_required=fee.is_required,
            )
            db.add(f)

        await db.flush()
        await db.refresh(product)
        return product

    @staticmethod
    async def get_product(
        db: AsyncSession, org_id: uuid.UUID, product_id: uuid.UUID,
    ) -> CreditProduct:
        result = await db.execute(
            select(CreditProduct).where(
                CreditProduct.id == product_id,
                CreditProduct.organization_id == org_id,
            )
        )
        product = result.scalar_one_or_none()
        if product is None:
            raise NotFoundError("Credit product not found.")
        return product

    @staticmethod
    async def update_product(
        db: AsyncSession, org_id: uuid.UUID, product_id: uuid.UUID, data: CreditProductUpdate,
    ) -> CreditProduct:
        product = await CreditProductService.get_product(db, org_id, product_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(product, field, value)
        await db.flush()
        await db.refresh(product)
        return product
