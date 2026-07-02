"""Motor de disponibilidad de SavvyHotel.

Regla de solape: una reserva ocupa una habitación en [check_in, check_out) si
    reserva.check_in_date < consulta.check_out  Y  reserva.check_out_date > consulta.check_in
y su estado es 'confirmed' o 'checked_in' (las canceladas/no_show/checked_out no ocupan).

Esto es lo que previene el overbooking.
"""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hotel.models import HotelReservation, HotelRoom, HotelRoomType

OCCUPYING = ("confirmed", "checked_in")


def _overlaps(check_in: date, check_out: date):
    return and_(
        HotelReservation.check_in_date < check_out,
        HotelReservation.check_out_date > check_in,
        HotelReservation.status.in_(OCCUPYING),
    )


async def occupied_room_ids(
    db: AsyncSession, org_id: uuid.UUID, check_in: date, check_out: date,
    exclude_reservation_id: uuid.UUID | None = None,
) -> set[uuid.UUID]:
    """IDs de habitaciones con reserva (asignada) que se solapa con el rango."""
    q = select(HotelReservation.room_id).where(
        HotelReservation.organization_id == org_id,
        HotelReservation.room_id.isnot(None),
        _overlaps(check_in, check_out),
    )
    if exclude_reservation_id:
        q = q.where(HotelReservation.id != exclude_reservation_id)
    return {r for (r,) in (await db.execute(q)).all() if r}


async def count_overlapping_by_type(
    db: AsyncSession, org_id: uuid.UUID, check_in: date, check_out: date,
) -> dict[uuid.UUID, int]:
    """Cuántas reservas ocupantes hay por tipo (asignadas o no) en el rango.

    Cuenta TODAS las reservas ocupantes del tipo, tengan o no habitación asignada,
    porque una reserva sin habitación asignada igual consume inventario del tipo.
    """
    q = (
        select(HotelReservation.room_type_id, func.count())
        .where(
            HotelReservation.organization_id == org_id,
            _overlaps(check_in, check_out),
        )
        .group_by(HotelReservation.room_type_id)
    )
    return {t: n for t, n in (await db.execute(q)).all()}


async def availability_by_type(
    db: AsyncSession, org_id: uuid.UUID, check_in: date, check_out: date,
) -> list[dict]:
    """Disponibilidad por tipo: total de habitaciones - reservas ocupantes."""
    # Total de habitaciones operativas por tipo (excluye mantenimiento/bloqueadas).
    rooms_q = (
        select(HotelRoom.room_type_id, func.count())
        .where(
            HotelRoom.organization_id == org_id,
            HotelRoom.status.notin_(("maintenance", "blocked")),
        )
        .group_by(HotelRoom.room_type_id)
    )
    totals = {t: n for t, n in (await db.execute(rooms_q)).all()}
    occupied = await count_overlapping_by_type(db, org_id, check_in, check_out)

    types = (await db.execute(
        select(HotelRoomType).where(
            HotelRoomType.organization_id == org_id,
            HotelRoomType.status == "active",
        ).order_by(HotelRoomType.name)
    )).scalars().all()

    rows: list[dict] = []
    for t in types:
        total = totals.get(t.id, 0)
        used = occupied.get(t.id, 0)
        rows.append({
            "room_type_id": t.id,
            "room_type_name": t.name,
            "base_rate": float(t.base_rate),
            "total_rooms": total,
            "available": max(total - used, 0),
        })
    return rows


async def available_rooms(
    db: AsyncSession, org_id: uuid.UUID, check_in: date, check_out: date,
    room_type_id: uuid.UUID | None = None,
    exclude_reservation_id: uuid.UUID | None = None,
) -> list[HotelRoom]:
    """Habitaciones concretas libres en el rango (para asignar)."""
    occ = await occupied_room_ids(db, org_id, check_in, check_out, exclude_reservation_id)
    q = select(HotelRoom).where(
        HotelRoom.organization_id == org_id,
        HotelRoom.status.notin_(("maintenance", "blocked")),
    )
    if room_type_id:
        q = q.where(HotelRoom.room_type_id == room_type_id)
    rooms = (await db.execute(q.order_by(HotelRoom.number))).scalars().all()
    return [r for r in rooms if r.id not in occ]


async def type_has_availability(
    db: AsyncSession, org_id: uuid.UUID, room_type_id: uuid.UUID,
    check_in: date, check_out: date, exclude_reservation_id: uuid.UUID | None = None,
) -> bool:
    """¿Hay al menos una habitación libre de ese tipo en el rango?"""
    rows = await availability_by_type(db, org_id, check_in, check_out)
    base = next((r for r in rows if r["room_type_id"] == room_type_id), None)
    if base is None:
        return False
    avail = base["available"]
    if exclude_reservation_id:
        # Si la reserva excluida es de este tipo y ocupa el rango, libera un cupo.
        from src.apps.hotel.models import HotelReservation as _R
        r = await db.get(_R, exclude_reservation_id)
        if r and r.room_type_id == room_type_id and r.status in OCCUPYING and \
           r.check_in_date < check_out and r.check_out_date > check_in:
            avail += 1
    return avail > 0
