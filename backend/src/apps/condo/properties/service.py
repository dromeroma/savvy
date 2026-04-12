"""Business logic for condo properties."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.condo.properties.models import CondoProperty, CondoUnit
from src.apps.condo.properties.schemas import PropertyCreate, UnitCreate


class PropertyService:
    @staticmethod
    async def list_properties(db: AsyncSession, org_id: uuid.UUID) -> list[CondoProperty]:
        return list((await db.execute(select(CondoProperty).where(CondoProperty.organization_id == org_id).order_by(CondoProperty.name))).scalars().all())

    @staticmethod
    async def create_property(db: AsyncSession, org_id: uuid.UUID, data: PropertyCreate) -> CondoProperty:
        p = CondoProperty(organization_id=org_id, **data.model_dump())
        db.add(p); await db.flush(); await db.refresh(p); return p

    @staticmethod
    async def list_units(db: AsyncSession, org_id: uuid.UUID, property_id: uuid.UUID | None = None) -> list[CondoUnit]:
        q = select(CondoUnit).where(CondoUnit.organization_id == org_id)
        if property_id: q = q.where(CondoUnit.property_id == property_id)
        return list((await db.execute(q.order_by(CondoUnit.code))).scalars().all())

    @staticmethod
    async def create_unit(db: AsyncSession, org_id: uuid.UUID, data: UnitCreate) -> CondoUnit:
        u = CondoUnit(organization_id=org_id, **data.model_dump())
        db.add(u); await db.flush(); await db.refresh(u); return u
