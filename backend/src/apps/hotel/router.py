"""SavvyHotel REST endpoints."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hotel import availability as avail
from src.apps.hotel.dashboard import hotel_dashboard
from src.apps.hotel.schemas import (
    AvailabilityResponse,
    ChargeFromPosRequest,
    CheckInRequest,
    FolioChargeCreate,
    FolioPaymentCreate,
    FolioResponse,
    HotelDashboard,
    HousekeepingUpdate,
    ReservationCreate,
    ReservationResponse,
    RoomCreate,
    RoomResponse,
    RoomTypeCreate,
    RoomTypeResponse,
    RoomTypeUpdate,
    RoomUpdate,
)
from src.apps.hotel.service import (
    FolioService,
    ReservationService,
    RoomService,
    RoomTypeService,
)
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(
    prefix="/hotel",
    tags=["SavvyHotel"],
    dependencies=[Depends(require_permission("hotel", "hotel.view", "hotel.manage"))],
)
_WRITE = [Depends(require_permission("hotel", "hotel.manage"))]


# ------------------------------ Dashboard ------------------------------

@router.get("/dashboard", response_model=HotelDashboard)
async def dashboard(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await hotel_dashboard(db, org_id)


# ------------------------------ Room types ------------------------------

@router.get("/room-types", response_model=list[RoomTypeResponse])
async def list_room_types(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomTypeService.list(db, org_id)


@router.post("/room-types", response_model=RoomTypeResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_room_type(data: RoomTypeCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomTypeService.create(db, org_id, data)


@router.patch("/room-types/{tid}", response_model=RoomTypeResponse, dependencies=_WRITE)
async def update_room_type(tid: uuid.UUID, data: RoomTypeUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomTypeService.update(db, org_id, tid, data)


# -------------------------------- Rooms --------------------------------

@router.get("/rooms", response_model=list[RoomResponse])
async def list_rooms(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomService.list(db, org_id)


@router.post("/rooms", response_model=RoomResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_room(data: RoomCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomService.create(db, org_id, data)


@router.patch("/rooms/{rid}", response_model=RoomResponse, dependencies=_WRITE)
async def update_room(rid: uuid.UUID, data: RoomUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomService.update(db, org_id, rid, data)


@router.post("/rooms/{rid}/housekeeping", response_model=RoomResponse, dependencies=_WRITE)
async def set_housekeeping(rid: uuid.UUID, data: HousekeepingUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await RoomService.set_housekeeping(db, org_id, rid, data.housekeeping_status)


# ----------------------------- Availability -----------------------------

@router.get("/availability", response_model=AvailabilityResponse)
async def get_availability(
    check_in: date = Query(...), check_out: date = Query(...),
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    rows = await avail.availability_by_type(db, org_id, check_in, check_out)
    return {"check_in": check_in, "check_out": check_out,
            "nights": max((check_out - check_in).days, 0), "rows": rows}


@router.get("/available-rooms", response_model=list[RoomResponse])
async def get_available_rooms(
    check_in: date = Query(...), check_out: date = Query(...),
    room_type_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    rooms = await avail.available_rooms(db, org_id, check_in, check_out, room_type_id)
    return [
        {**{c.name: getattr(r, c.name) for c in r.__table__.columns}, "room_type_name": None}
        for r in rooms
    ]


# ----------------------------- Reservations -----------------------------

@router.get("/reservations", response_model=list[ReservationResponse])
async def list_reservations(
    status_f: str | None = Query(None, alias="status"),
    date_from: date | None = Query(None), date_to: date | None = Query(None),
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReservationService.list(db, org_id, status_f, date_from, date_to)


@router.post("/reservations", response_model=ReservationResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_reservation(data: ReservationCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ReservationService.create(db, org_id, data)


@router.post("/reservations/{rid}/check-in", response_model=ReservationResponse, dependencies=_WRITE)
async def check_in(rid: uuid.UUID, data: CheckInRequest, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ReservationService.check_in(db, org_id, rid, data.room_id)


@router.post("/reservations/{rid}/check-out", response_model=ReservationResponse, dependencies=_WRITE)
async def check_out(rid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ReservationService.check_out(db, org_id, rid)


@router.post("/reservations/{rid}/cancel", response_model=ReservationResponse, dependencies=_WRITE)
async def cancel_reservation(rid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ReservationService.set_status(db, org_id, rid, "cancelled")


@router.post("/reservations/{rid}/no-show", response_model=ReservationResponse, dependencies=_WRITE)
async def mark_no_show(rid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ReservationService.set_status(db, org_id, rid, "no_show")


# -------------------------------- Folio --------------------------------

@router.get("/reservations/{rid}/folio", response_model=FolioResponse)
async def get_folio(rid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await FolioService.get(db, org_id, rid)


@router.post("/reservations/{rid}/folio/charges", response_model=FolioResponse, dependencies=_WRITE)
async def add_charge(rid: uuid.UUID, data: FolioChargeCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await FolioService.add_charge(db, org_id, rid, data)


@router.post("/reservations/{rid}/folio/charge-from-pos", response_model=FolioResponse, dependencies=_WRITE)
async def charge_from_pos(rid: uuid.UUID, data: ChargeFromPosRequest, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await FolioService.charge_from_pos(db, org_id, rid, data.sale_id)


@router.post("/reservations/{rid}/folio/payments", response_model=FolioResponse, dependencies=_WRITE)
async def add_payment(rid: uuid.UUID, data: FolioPaymentCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await FolioService.add_payment(db, org_id, rid, data)
