"""Hotel demo aislado: org + usuario owner + app hotel + tipos/habitaciones/reservas.

Login:
    email:    admin@hotel-demo.com
    password: Hotel1234!

Idempotente en la parte de org/usuario/app; resetea los datos de hotel de la org.

Uso: python backend/scripts/seed_hotel_demo.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import date, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import src.gateway.router  # noqa: E402,F401
from sqlalchemy import text  # noqa: E402

from src.apps.hotel.schemas import ReservationCreate, RoomCreate, RoomTypeCreate  # noqa: E402
from src.apps.hotel.service import ReservationService, RoomService, RoomTypeService  # noqa: E402
from src.core.database import async_session_factory, engine  # noqa: E402
from src.core.security import hash_password  # noqa: E402

ORG_SLUG = "hotel-demo"
ORG_NAME = "Hotel Brisa del Mar"
EMAIL = "admin@hotel-demo.com"
PASSWORD = "Hotel1234!"

TYPES = [
    ("SEN", "Sencilla", 1, 90000, ["WiFi", "TV"]),
    ("DOB", "Doble", 2, 140000, ["WiFi", "TV", "Nevera"]),
    ("SUI", "Suite", 4, 260000, ["WiFi", "TV", "Nevera", "Jacuzzi"]),
]
# (numero, piso, tipo_idx)
ROOMS = [("101", "1", 0), ("102", "1", 0), ("103", "1", 1),
         ("104", "1", 1), ("201", "2", 1), ("202", "2", 1),
         ("301", "3", 2), ("302", "3", 2)]


async def main() -> None:
    print("=" * 70)
    print("SavvyHotel · seed de hotel demo")
    print("=" * 70)
    async with async_session_factory() as s:
        org = await s.scalar(text("SELECT id FROM organizations WHERE slug=:sl"), {"sl": ORG_SLUG})
        if not org:
            org = uuid.uuid4()
            await s.execute(text(
                "INSERT INTO organizations (id,name,slug,type,settings,created_at,updated_at) "
                "VALUES (:i,:n,:sl,'business','{}'::jsonb,now(),now())"),
                {"i": org, "n": ORG_NAME, "sl": ORG_SLUG})
            print(f"  + org {ORG_NAME}")
        else:
            await s.execute(text("UPDATE organizations SET name=:n WHERE id=:i"), {"n": ORG_NAME, "i": org})

        uid = await s.scalar(text("SELECT id FROM public.users WHERE email=:e"), {"e": EMAIL})
        if not uid:
            uid = uuid.uuid4()
            await s.execute(text(
                "INSERT INTO public.users (id,name,email,password_hash,created_at,updated_at) "
                "VALUES (:i,:n,:e,:p,now(),now())"),
                {"i": uid, "n": "Recepción", "e": EMAIL, "p": hash_password(PASSWORD)})
            print(f"  + usuario {EMAIL}")
        else:
            await s.execute(text("UPDATE public.users SET password_hash=:p WHERE id=:i"),
                            {"p": hash_password(PASSWORD), "i": uid})

        if not await s.scalar(text("SELECT 1 FROM memberships WHERE organization_id=:o AND user_id=:u"), {"o": org, "u": uid}):
            await s.execute(text(
                "INSERT INTO memberships (id,organization_id,user_id,role,joined_at,created_at,updated_at) "
                "VALUES (:i,:o,:u,'owner',now(),now(),now())"), {"i": uuid.uuid4(), "o": org, "u": uid})
            print("  + membresía owner")

        app_id = await s.scalar(text("SELECT id FROM app_registry WHERE code='hotel'"))
        if not await s.scalar(text("SELECT 1 FROM organization_apps WHERE organization_id=:o AND app_id=:a"), {"o": org, "a": app_id}):
            await s.execute(text(
                "INSERT INTO organization_apps (id,organization_id,app_id,status,activated_at,settings,created_at,updated_at) "
                "VALUES (:i,:o,:a,'active',now(),'{}'::jsonb,now(),now())"), {"i": uuid.uuid4(), "o": org, "a": app_id})
            print("  + app hotel activada")

        # reset datos de hotel de la org
        for t in ["hotel_folio_payments", "hotel_folio_charges", "hotel_folios",
                  "hotel_reservations", "hotel_rooms", "hotel_room_types"]:
            await s.execute(text(f"DELETE FROM {t} WHERE organization_id=:o"), {"o": org})
        await s.commit()

        # tipos + habitaciones
        type_ids = []
        for code, name, cap, rate, am in TYPES:
            t = await RoomTypeService.create(s, org, RoomTypeCreate(code=code, name=name, capacity=cap, base_rate=rate, amenities=am))
            type_ids.append(t.id)
        for num, floor, ti in ROOMS:
            await RoomService.create(s, org, RoomCreate(room_type_id=type_ids[ti], number=num, floor=floor))
        await s.commit()
        print(f"  + {len(TYPES)} tipos · {len(ROOMS)} habitaciones")

    today = date.today()
    # reserva llegando hoy (confirmada)
    async with async_session_factory() as s:
        org = await s.scalar(text("SELECT id FROM organizations WHERE slug=:sl"), {"sl": ORG_SLUG})
        types = (await s.execute(text("SELECT id FROM hotel_room_types WHERE organization_id=:o ORDER BY base_rate"), {"o": org})).scalars().all()
        r1 = await ReservationService.create(s, org, ReservationCreate(
            guest_name="Carlos Ramírez", guest_document="94123456", room_type_id=types[1],
            check_in_date=today, check_out_date=today + timedelta(days=3), adults=2))
        await s.commit()
        rid1 = uuid.UUID(str(r1["id"]))
    # esa reserva: check-in (queda en casa)
    async with async_session_factory() as s:
        org = await s.scalar(text("SELECT id FROM organizations WHERE slug=:sl"), {"sl": ORG_SLUG})
        from src.apps.hotel import availability as av
        r = await s.get(__import__("src.apps.hotel.models", fromlist=["HotelReservation"]).HotelReservation, rid1)
        free = await av.available_rooms(s, org, r.check_in_date, r.check_out_date, r.room_type_id, exclude_reservation_id=rid1)
        if free:
            await ReservationService.check_in(s, org, rid1, free[0].id)
            await s.commit()
    # reserva futura (confirmada)
    async with async_session_factory() as s:
        org = await s.scalar(text("SELECT id FROM organizations WHERE slug=:sl"), {"sl": ORG_SLUG})
        types = (await s.execute(text("SELECT id FROM hotel_room_types WHERE organization_id=:o ORDER BY base_rate"), {"o": org})).scalars().all()
        await ReservationService.create(s, org, ReservationCreate(
            guest_name="Laura Méndez", guest_document="52987654", room_type_id=types[2],
            check_in_date=today + timedelta(days=5), check_out_date=today + timedelta(days=7), adults=2, children=1))
        await s.commit()
        print("  + 2 reservas (1 en casa, 1 futura)")

    print(f"\n✓ Hotel demo listo. Login: {EMAIL} / {PASSWORD}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
