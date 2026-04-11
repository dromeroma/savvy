"""Business logic for parking infrastructure."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.parking.infrastructure.models import ParkingLocation, ParkingSpot, ParkingZone
from src.apps.parking.infrastructure.schemas import LocationCreate, SpotCreate, ZoneCreate


class InfrastructureService:

    @staticmethod
    async def list_locations(db: AsyncSession, org_id: uuid.UUID) -> list[ParkingLocation]:
        return list((await db.execute(select(ParkingLocation).where(ParkingLocation.organization_id == org_id).order_by(ParkingLocation.name))).scalars().all())

    @staticmethod
    async def create_location(db: AsyncSession, org_id: uuid.UUID, data: LocationCreate) -> ParkingLocation:
        loc = ParkingLocation(organization_id=org_id, **data.model_dump())
        db.add(loc)
        await db.flush()
        await db.refresh(loc)
        return loc

    @staticmethod
    async def list_zones(db: AsyncSession, org_id: uuid.UUID, location_id: uuid.UUID | None = None) -> list[ParkingZone]:
        q = select(ParkingZone).where(ParkingZone.organization_id == org_id)
        if location_id:
            q = q.where(ParkingZone.location_id == location_id)
        return list((await db.execute(q.order_by(ParkingZone.name))).scalars().all())

    @staticmethod
    async def create_zone(db: AsyncSession, org_id: uuid.UUID, data: ZoneCreate) -> ParkingZone:
        zone = ParkingZone(organization_id=org_id, **data.model_dump())
        db.add(zone)
        await db.flush()
        await db.refresh(zone)
        return zone

    @staticmethod
    async def list_spots(db: AsyncSession, org_id: uuid.UUID, zone_id: uuid.UUID | None = None, status_filter: str | None = None) -> list[ParkingSpot]:
        q = select(ParkingSpot).where(ParkingSpot.organization_id == org_id)
        if zone_id:
            q = q.where(ParkingSpot.zone_id == zone_id)
        if status_filter:
            q = q.where(ParkingSpot.status == status_filter)
        return list((await db.execute(q.order_by(ParkingSpot.code))).scalars().all())

    @staticmethod
    async def create_spot(db: AsyncSession, org_id: uuid.UUID, data: SpotCreate) -> ParkingSpot:
        spot = ParkingSpot(organization_id=org_id, **data.model_dump())
        db.add(spot)
        await db.flush()
        await db.refresh(spot)
        return spot

    @staticmethod
    async def update_spot_status(db: AsyncSession, org_id: uuid.UUID, spot_id: uuid.UUID, status: str) -> ParkingSpot:
        result = await db.execute(select(ParkingSpot).where(ParkingSpot.id == spot_id, ParkingSpot.organization_id == org_id))
        spot = result.scalar_one_or_none()
        if spot is None:
            raise NotFoundError("Spot not found.")
        spot.status = status
        await db.flush()
        await db.refresh(spot)
        return spot
