"""Business logic for POS config."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.pos.config.models import PosDiscount, PosTax
from src.apps.pos.config.schemas import DiscountCreate, TaxCreate


class ConfigService:

    @staticmethod
    async def list_taxes(db: AsyncSession, org_id: uuid.UUID) -> list[PosTax]:
        return list((await db.execute(select(PosTax).where(PosTax.organization_id == org_id).order_by(PosTax.name))).scalars().all())

    @staticmethod
    async def create_tax(db: AsyncSession, org_id: uuid.UUID, data: TaxCreate) -> PosTax:
        t = PosTax(organization_id=org_id, **data.model_dump())
        db.add(t); await db.flush(); await db.refresh(t); return t

    @staticmethod
    async def list_discounts(db: AsyncSession, org_id: uuid.UUID) -> list[PosDiscount]:
        return list((await db.execute(select(PosDiscount).where(PosDiscount.organization_id == org_id).order_by(PosDiscount.name))).scalars().all())

    @staticmethod
    async def create_discount(db: AsyncSession, org_id: uuid.UUID, data: DiscountCreate) -> PosDiscount:
        d = PosDiscount(organization_id=org_id, **data.model_dump())
        db.add(d); await db.flush(); await db.refresh(d); return d
