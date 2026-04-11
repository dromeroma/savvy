"""Business logic for parking vehicles."""

from __future__ import annotations
import uuid
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.parking.vehicles.models import ParkingVehicle
from src.apps.parking.vehicles.schemas import VehicleCreate


class VehicleService:

    @staticmethod
    async def list_vehicles(db: AsyncSession, org_id: uuid.UUID, search: str | None = None) -> list[ParkingVehicle]:
        q = select(ParkingVehicle).where(ParkingVehicle.organization_id == org_id)
        if search:
            q = q.where(or_(ParkingVehicle.plate.ilike(f"%{search}%"), ParkingVehicle.brand.ilike(f"%{search}%")))
        return list((await db.execute(q.order_by(ParkingVehicle.plate))).scalars().all())

    @staticmethod
    async def create_vehicle(db: AsyncSession, org_id: uuid.UUID, data: VehicleCreate) -> ParkingVehicle:
        v = ParkingVehicle(organization_id=org_id, **data.model_dump())
        db.add(v)
        await db.flush()
        await db.refresh(v)
        return v

    @staticmethod
    async def find_by_plate(db: AsyncSession, org_id: uuid.UUID, plate: str) -> ParkingVehicle | None:
        result = await db.execute(select(ParkingVehicle).where(ParkingVehicle.organization_id == org_id, ParkingVehicle.plate == plate.upper()))
        return result.scalar_one_or_none()
