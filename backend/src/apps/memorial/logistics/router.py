"""Endpoints REST para catálogos de logística."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.logistics.schemas import (
    DriverCreate, DriverResponse, DriverUpdate,
    LocationCreate, LocationResponse, LocationUpdate,
    OvenCreate, OvenResponse, OvenUpdate,
    RoomCreate, RoomResponse, RoomUpdate,
    VehicleCreate, VehicleResponse, VehicleUpdate,
)
from src.apps.memorial.logistics.service import (
    DriversService, LocationsService, OvensService, RoomsService, VehiclesService,
)
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission


def _perm_read():
    return Depends(require_permission(
        "memorial", "logistics.read", "logistics.manage",
        "services.read", "services.manage",
    ))


def _perm_manage():
    return Depends(require_permission("memorial", "logistics.manage"))


router = APIRouter(prefix="/logistics", tags=["Memorial · Logística"])


# ---------------------------------------------------------------- Vehicles


@router.get("/vehicles", response_model=list[VehicleResponse], dependencies=[_perm_read()])
async def list_vehicles(
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await VehiclesService.list_(db, org_id, search=search)


@router.get("/vehicles/{vid}", response_model=VehicleResponse, dependencies=[_perm_read()])
async def get_vehicle(vid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await VehiclesService.get(db, org_id, vid)


@router.post("/vehicles", response_model=VehicleResponse, status_code=status.HTTP_201_CREATED, dependencies=[_perm_manage()])
async def create_vehicle(data: VehicleCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await VehiclesService.create(db, org_id, data)


@router.patch("/vehicles/{vid}", response_model=VehicleResponse, dependencies=[_perm_manage()])
async def update_vehicle(vid: uuid.UUID, data: VehicleUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await VehiclesService.update(db, org_id, vid, data)


@router.delete("/vehicles/{vid}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, dependencies=[_perm_manage()])
async def delete_vehicle(vid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> None:
    await VehiclesService.delete(db, org_id, vid)


# ---------------------------------------------------------------- Drivers


@router.get("/drivers", response_model=list[DriverResponse], dependencies=[_perm_read()])
async def list_drivers(search: str | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await DriversService.list_(db, org_id, search=search)


@router.get("/drivers/{did}", response_model=DriverResponse, dependencies=[_perm_read()])
async def get_driver(did: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await DriversService.get(db, org_id, did)


@router.post("/drivers", response_model=DriverResponse, status_code=status.HTTP_201_CREATED, dependencies=[_perm_manage()])
async def create_driver(data: DriverCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await DriversService.create(db, org_id, data)


@router.patch("/drivers/{did}", response_model=DriverResponse, dependencies=[_perm_manage()])
async def update_driver(did: uuid.UUID, data: DriverUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await DriversService.update(db, org_id, did, data)


@router.delete("/drivers/{did}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, dependencies=[_perm_manage()])
async def delete_driver(did: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> None:
    await DriversService.delete(db, org_id, did)


# ---------------------------------------------------------------- Rooms


@router.get("/rooms", response_model=list[RoomResponse], dependencies=[_perm_read()])
async def list_rooms(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomsService.list_(db, org_id)


@router.get("/rooms/{rid}", response_model=RoomResponse, dependencies=[_perm_read()])
async def get_room(rid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomsService.get(db, org_id, rid)


@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED, dependencies=[_perm_manage()])
async def create_room(data: RoomCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomsService.create(db, org_id, data)


@router.patch("/rooms/{rid}", response_model=RoomResponse, dependencies=[_perm_manage()])
async def update_room(rid: uuid.UUID, data: RoomUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomsService.update(db, org_id, rid, data)


@router.delete("/rooms/{rid}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, dependencies=[_perm_manage()])
async def delete_room(rid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> None:
    await RoomsService.delete(db, org_id, rid)


# ---------------------------------------------------------------- Ovens


@router.get("/ovens", response_model=list[OvenResponse], dependencies=[_perm_read()])
async def list_ovens(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await OvensService.list_(db, org_id)


@router.get("/ovens/{oid}", response_model=OvenResponse, dependencies=[_perm_read()])
async def get_oven(oid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await OvensService.get(db, org_id, oid)


@router.post("/ovens", response_model=OvenResponse, status_code=status.HTTP_201_CREATED, dependencies=[_perm_manage()])
async def create_oven(data: OvenCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await OvensService.create(db, org_id, data)


@router.patch("/ovens/{oid}", response_model=OvenResponse, dependencies=[_perm_manage()])
async def update_oven(oid: uuid.UUID, data: OvenUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await OvensService.update(db, org_id, oid, data)


@router.delete("/ovens/{oid}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, dependencies=[_perm_manage()])
async def delete_oven(oid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> None:
    await OvensService.delete(db, org_id, oid)


# ---------------------------------------------------------------- Locations


@router.get("/locations", response_model=list[LocationResponse], dependencies=[_perm_read()])
async def list_locations(
    kind: str | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LocationsService.list_(db, org_id, kind=kind, search=search)


@router.get("/locations/{lid}", response_model=LocationResponse, dependencies=[_perm_read()])
async def get_location(lid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LocationsService.get(db, org_id, lid)


@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED, dependencies=[_perm_manage()])
async def create_location(data: LocationCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LocationsService.create(db, org_id, data)


@router.patch("/locations/{lid}", response_model=LocationResponse, dependencies=[_perm_manage()])
async def update_location(lid: uuid.UUID, data: LocationUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LocationsService.update(db, org_id, lid, data)


@router.delete("/locations/{lid}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, dependencies=[_perm_manage()])
async def delete_location(lid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> None:
    await LocationsService.delete(db, org_id, lid)
