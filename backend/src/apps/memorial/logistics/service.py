"""Logística — CRUD genérico para los 5 catálogos. Sin reglas de negocio
sofisticadas porque cada catálogo es una entidad sencilla."""

from __future__ import annotations

import uuid

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import func

from src.apps.memorial.logistics.schemas import (
    DriverCreate,
    DriverUpdate,
    LocationCreate,
    LocationUpdate,
    OvenCreate,
    OvenUpdate,
    RoomCreate,
    RoomUpdate,
    VehicleCreate,
    VehicleUpdate,
)
from src.apps.memorial.models import (
    MemorialDriver,
    MemorialLocation,
    MemorialOven,
    MemorialRoom,
    MemorialTransfer,
    MemorialVehicle,
)
from src.core.exceptions import ConflictError, NotFoundError


async def _ensure_unique_code(db, org_id, model, code, exclude_id=None) -> None:
    stmt = select(model).where(
        model.organization_id == org_id,
        model.code == code,
    )
    if exclude_id:
        stmt = stmt.where(model.id != exclude_id)
    existing = await db.scalar(stmt)
    if existing is not None:
        raise ConflictError(f"Ya existe un registro con código '{code}'.")


# ---------------------------------------------------------------- Vehicles


class VehiclesService:

    @staticmethod
    async def list_(db: AsyncSession, org_id: uuid.UUID, search: str | None = None):
        stmt = (
            select(MemorialVehicle)
            .where(MemorialVehicle.organization_id == org_id)
            .order_by(MemorialVehicle.code)
        )
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(MemorialVehicle.code).like(like),
                    func.lower(MemorialVehicle.plate).like(like),
                    func.lower(func.coalesce(MemorialVehicle.brand, "")).like(like),
                    func.lower(func.coalesce(MemorialVehicle.model, "")).like(like),
                )
            )
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db, org_id, vid):
        v = await db.scalar(
            select(MemorialVehicle).where(
                MemorialVehicle.id == vid,
                MemorialVehicle.organization_id == org_id,
            )
        )
        if v is None:
            raise NotFoundError("Vehículo no encontrado.")
        return v

    @staticmethod
    async def create(db, org_id, data: VehicleCreate):
        await _ensure_unique_code(db, org_id, MemorialVehicle, data.code)
        v = MemorialVehicle(organization_id=org_id, **data.model_dump())
        db.add(v)
        await db.flush()
        await db.refresh(v)
        return v

    @staticmethod
    async def update(db, org_id, vid, data: VehicleUpdate):
        v = await VehiclesService.get(db, org_id, vid)
        for k, val in data.model_dump(exclude_unset=True).items():
            setattr(v, k, val)
        await db.flush()
        await db.refresh(v)
        return v

    @staticmethod
    async def delete(db, org_id, vid):
        # Bloquear si está usado en algún traslado
        in_use = await db.scalar(
            select(func.count(MemorialTransfer.id)).where(
                MemorialTransfer.vehicle_id == vid,
            )
        )
        if int(in_use or 0) > 0:
            raise ConflictError(
                "Vehículo en uso por traslados — desactívalo en vez de eliminarlo.",
            )
        v = await VehiclesService.get(db, org_id, vid)
        await db.delete(v)
        await db.flush()


# ---------------------------------------------------------------- Drivers


class DriversService:

    @staticmethod
    async def list_(db, org_id, search=None):
        stmt = (
            select(MemorialDriver)
            .where(MemorialDriver.organization_id == org_id)
            .order_by(MemorialDriver.code)
        )
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(MemorialDriver.code).like(like),
                    func.lower(MemorialDriver.first_name).like(like),
                    func.lower(func.coalesce(MemorialDriver.last_name, "")).like(like),
                    func.lower(func.coalesce(MemorialDriver.license_number, "")).like(like),
                )
            )
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db, org_id, did):
        d = await db.scalar(
            select(MemorialDriver).where(
                MemorialDriver.id == did,
                MemorialDriver.organization_id == org_id,
            )
        )
        if d is None:
            raise NotFoundError("Conductor no encontrado.")
        return d

    @staticmethod
    async def create(db, org_id, data: DriverCreate):
        await _ensure_unique_code(db, org_id, MemorialDriver, data.code)
        d = MemorialDriver(organization_id=org_id, **data.model_dump())
        db.add(d)
        await db.flush()
        await db.refresh(d)
        return d

    @staticmethod
    async def update(db, org_id, did, data: DriverUpdate):
        d = await DriversService.get(db, org_id, did)
        for k, val in data.model_dump(exclude_unset=True).items():
            setattr(d, k, val)
        await db.flush()
        await db.refresh(d)
        return d

    @staticmethod
    async def delete(db, org_id, did):
        in_use = await db.scalar(
            select(func.count(MemorialTransfer.id)).where(
                MemorialTransfer.driver_id == did,
            )
        )
        if int(in_use or 0) > 0:
            raise ConflictError(
                "Conductor con traslados asignados — desactívalo en vez de eliminarlo.",
            )
        d = await DriversService.get(db, org_id, did)
        await db.delete(d)
        await db.flush()


# ---------------------------------------------------------------- Rooms


class RoomsService:

    @staticmethod
    async def list_(db, org_id):
        rows = await db.execute(
            select(MemorialRoom)
            .where(MemorialRoom.organization_id == org_id)
            .order_by(MemorialRoom.code)
        )
        return list(rows.scalars().all())

    @staticmethod
    async def get(db, org_id, rid):
        r = await db.scalar(
            select(MemorialRoom).where(
                MemorialRoom.id == rid,
                MemorialRoom.organization_id == org_id,
            )
        )
        if r is None:
            raise NotFoundError("Sala no encontrada.")
        return r

    @staticmethod
    async def create(db, org_id, data: RoomCreate):
        await _ensure_unique_code(db, org_id, MemorialRoom, data.code)
        r = MemorialRoom(organization_id=org_id, **data.model_dump())
        db.add(r)
        await db.flush()
        await db.refresh(r)
        return r

    @staticmethod
    async def update(db, org_id, rid, data: RoomUpdate):
        r = await RoomsService.get(db, org_id, rid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(r, k, v)
        await db.flush()
        await db.refresh(r)
        return r

    @staticmethod
    async def delete(db, org_id, rid):
        r = await RoomsService.get(db, org_id, rid)
        await db.delete(r)
        await db.flush()


# ---------------------------------------------------------------- Ovens


class OvensService:

    @staticmethod
    async def list_(db, org_id):
        rows = await db.execute(
            select(MemorialOven)
            .where(MemorialOven.organization_id == org_id)
            .order_by(MemorialOven.code)
        )
        return list(rows.scalars().all())

    @staticmethod
    async def get(db, org_id, oid):
        o = await db.scalar(
            select(MemorialOven).where(
                MemorialOven.id == oid,
                MemorialOven.organization_id == org_id,
            )
        )
        if o is None:
            raise NotFoundError("Horno no encontrado.")
        return o

    @staticmethod
    async def create(db, org_id, data: OvenCreate):
        await _ensure_unique_code(db, org_id, MemorialOven, data.code)
        o = MemorialOven(organization_id=org_id, **data.model_dump())
        db.add(o)
        await db.flush()
        await db.refresh(o)
        return o

    @staticmethod
    async def update(db, org_id, oid, data: OvenUpdate):
        o = await OvensService.get(db, org_id, oid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(o, k, v)
        await db.flush()
        await db.refresh(o)
        return o

    @staticmethod
    async def delete(db, org_id, oid):
        o = await OvensService.get(db, org_id, oid)
        await db.delete(o)
        await db.flush()


# ---------------------------------------------------------------- Locations


class LocationsService:

    @staticmethod
    async def list_(db, org_id, kind: str | None = None, search: str | None = None):
        stmt = (
            select(MemorialLocation)
            .where(MemorialLocation.organization_id == org_id)
            .order_by(MemorialLocation.kind, MemorialLocation.code)
        )
        if kind:
            stmt = stmt.where(MemorialLocation.kind == kind)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(MemorialLocation.code).like(like),
                    func.lower(MemorialLocation.name).like(like),
                    func.lower(func.coalesce(MemorialLocation.city, "")).like(like),
                )
            )
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db, org_id, lid):
        loc = await db.scalar(
            select(MemorialLocation).where(
                MemorialLocation.id == lid,
                MemorialLocation.organization_id == org_id,
            )
        )
        if loc is None:
            raise NotFoundError("Lugar no encontrado.")
        return loc

    @staticmethod
    async def create(db, org_id, data: LocationCreate):
        await _ensure_unique_code(db, org_id, MemorialLocation, data.code)
        loc = MemorialLocation(organization_id=org_id, **data.model_dump())
        db.add(loc)
        await db.flush()
        await db.refresh(loc)
        return loc

    @staticmethod
    async def update(db, org_id, lid, data: LocationUpdate):
        loc = await LocationsService.get(db, org_id, lid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(loc, k, v)
        await db.flush()
        await db.refresh(loc)
        return loc

    @staticmethod
    async def delete(db, org_id, lid):
        loc = await LocationsService.get(db, org_id, lid)
        await db.delete(loc)
        await db.flush()
