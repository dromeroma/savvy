"""SavvyHotel dashboard — ocupación, ADR, RevPAR, llegadas/salidas."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hotel.models import HotelFolioCharge, HotelReservation, HotelRoom

OCCUPYING = ("confirmed", "checked_in")


async def hotel_dashboard(db: AsyncSession, org_id: uuid.UUID) -> dict:
    today = datetime.now(UTC).date()

    total_rooms = int(await db.scalar(
        select(func.count()).select_from(HotelRoom).where(
            HotelRoom.organization_id == org_id,
            HotelRoom.status.notin_(("maintenance", "blocked")),
        )
    ) or 0)

    # En casa hoy: reservas checked_in que cubren la fecha de hoy.
    in_house = int(await db.scalar(
        select(func.count()).select_from(HotelReservation).where(
            HotelReservation.organization_id == org_id,
            HotelReservation.status == "checked_in",
        )
    ) or 0)

    # Ocupadas hoy = reservas ocupantes que cubren hoy.
    occupied = int(await db.scalar(
        select(func.count()).select_from(HotelReservation).where(
            HotelReservation.organization_id == org_id,
            HotelReservation.status == "checked_in",
            HotelReservation.check_in_date <= today,
            HotelReservation.check_out_date > today,
        )
    ) or 0)

    arrivals = int(await db.scalar(
        select(func.count()).select_from(HotelReservation).where(
            HotelReservation.organization_id == org_id,
            HotelReservation.check_in_date == today,
            HotelReservation.status.in_(OCCUPYING),
        )
    ) or 0)

    departures = int(await db.scalar(
        select(func.count()).select_from(HotelReservation).where(
            HotelReservation.organization_id == org_id,
            HotelReservation.check_out_date == today,
            HotelReservation.status.in_(("checked_in", "checked_out")),
        )
    ) or 0)

    # Ingreso de habitación de los que están en casa (para ADR/RevPAR).
    room_rev = float(await db.scalar(
        select(func.coalesce(func.sum(HotelReservation.rate), 0)).where(
            HotelReservation.organization_id == org_id,
            HotelReservation.status == "checked_in",
            HotelReservation.check_in_date <= today,
            HotelReservation.check_out_date > today,
        )
    ) or 0)

    dirty = int(await db.scalar(
        select(func.count()).select_from(HotelRoom).where(
            HotelRoom.organization_id == org_id,
            HotelRoom.housekeeping_status == "dirty",
        )
    ) or 0)

    revenue_today = float(await db.scalar(
        select(func.coalesce(func.sum(HotelFolioCharge.amount), 0)).where(
            HotelFolioCharge.organization_id == org_id,
            func.date(HotelFolioCharge.charged_at) == today,
        )
    ) or 0)

    occupancy_rate = round((occupied / total_rooms) * 100, 1) if total_rooms else 0.0
    adr = round(room_rev / occupied, 2) if occupied else 0.0
    revpar = round(room_rev / total_rooms, 2) if total_rooms else 0.0

    return {
        "total_rooms": total_rooms,
        "occupied_rooms": occupied,
        "occupancy_rate": occupancy_rate,
        "arrivals_today": arrivals,
        "departures_today": departures,
        "in_house": in_house,
        "adr": adr,
        "revpar": revpar,
        "revenue_today": revenue_today,
        "dirty_rooms": dirty,
    }
