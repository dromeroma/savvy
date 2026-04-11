"""Business logic for parking services."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.parking.services.models import ParkingServiceOrder, ParkingServiceType
from src.apps.parking.services.schemas import ServiceOrderCreate, ServiceTypeCreate


class ParkingServicesService:

    @staticmethod
    async def list_types(db: AsyncSession, org_id: uuid.UUID) -> list[ParkingServiceType]:
        return list((await db.execute(select(ParkingServiceType).where(ParkingServiceType.organization_id == org_id).order_by(ParkingServiceType.name))).scalars().all())

    @staticmethod
    async def create_type(db: AsyncSession, org_id: uuid.UUID, data: ServiceTypeCreate) -> ParkingServiceType:
        svc = ParkingServiceType(organization_id=org_id, **data.model_dump())
        db.add(svc)
        await db.flush()
        await db.refresh(svc)
        return svc

    @staticmethod
    async def create_order(db: AsyncSession, org_id: uuid.UUID, data: ServiceOrderCreate) -> ParkingServiceOrder:
        svc_result = await db.execute(select(ParkingServiceType).where(ParkingServiceType.id == data.service_id))
        svc = svc_result.scalar_one_or_none()
        if svc is None:
            raise NotFoundError("Service type not found.")
        order = ParkingServiceOrder(organization_id=org_id, service_id=data.service_id, session_id=data.session_id, vehicle_id=data.vehicle_id, price=float(svc.price), notes=data.notes)
        db.add(order)
        await db.flush()
        await db.refresh(order)
        return order

    @staticmethod
    async def list_orders(db: AsyncSession, org_id: uuid.UUID, session_id: uuid.UUID | None = None) -> list[ParkingServiceOrder]:
        q = select(ParkingServiceOrder).where(ParkingServiceOrder.organization_id == org_id)
        if session_id:
            q = q.where(ParkingServiceOrder.session_id == session_id)
        return list((await db.execute(q.order_by(ParkingServiceOrder.created_at.desc()))).scalars().all())

    @staticmethod
    async def complete_order(db: AsyncSession, org_id: uuid.UUID, order_id: uuid.UUID) -> ParkingServiceOrder:
        result = await db.execute(select(ParkingServiceOrder).where(ParkingServiceOrder.id == order_id, ParkingServiceOrder.organization_id == org_id))
        order = result.scalar_one_or_none()
        if order is None:
            raise NotFoundError("Order not found.")
        order.status = "completed"
        await db.flush()
        await db.refresh(order)
        return order
