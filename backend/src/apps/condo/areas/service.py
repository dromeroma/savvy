"""Business logic for condo common areas."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.condo.areas.models import CondoCommonArea, CondoReservation
from src.apps.condo.areas.schemas import CommonAreaCreate, ReservationCreate


class AreaService:
    @staticmethod
    async def list_areas(db: AsyncSession, org_id: uuid.UUID, property_id: uuid.UUID | None = None) -> list[CondoCommonArea]:
        q = select(CondoCommonArea).where(CondoCommonArea.organization_id == org_id)
        if property_id: q = q.where(CondoCommonArea.property_id == property_id)
        return list((await db.execute(q.order_by(CondoCommonArea.name))).scalars().all())

    @staticmethod
    async def create_area(db: AsyncSession, org_id: uuid.UUID, data: CommonAreaCreate) -> CondoCommonArea:
        a = CondoCommonArea(organization_id=org_id, **data.model_dump())
        db.add(a); await db.flush(); await db.refresh(a); return a

    @staticmethod
    async def list_reservations(db: AsyncSession, org_id: uuid.UUID, area_id: uuid.UUID | None = None) -> list[CondoReservation]:
        q = select(CondoReservation).where(CondoReservation.organization_id == org_id)
        if area_id: q = q.where(CondoReservation.area_id == area_id)
        return list((await db.execute(q.order_by(CondoReservation.reserved_from))).scalars().all())

    @staticmethod
    async def create_reservation(db: AsyncSession, org_id: uuid.UUID, data: ReservationCreate) -> CondoReservation:
        # Get area fee
        area_result = await db.execute(select(CondoCommonArea).where(CondoCommonArea.id == data.area_id))
        area = area_result.scalar_one_or_none()
        fee = float(area.reservation_fee) if area else 0
        r = CondoReservation(organization_id=org_id, fee=fee, **data.model_dump())
        db.add(r); await db.flush(); await db.refresh(r); return r
