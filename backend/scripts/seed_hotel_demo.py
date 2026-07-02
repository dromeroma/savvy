"""Hotel demo integral: SavvyHotel + Parqueo + Contabilidad, aislado por org.

Login:
    email:    admin@monterrey-center.com
    password: Monterrey1234!

Idempotente: migra el usuario/nombre previos y resetea los datos demo.

Uso: python backend/scripts/seed_hotel_demo.py
"""

from __future__ import annotations

import asyncio
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

import src.gateway.router  # noqa: E402,F401
from sqlalchemy import text  # noqa: E402

from src.apps.hotel import availability as av  # noqa: E402
from src.apps.hotel.models import HotelReservation  # noqa: E402
from src.apps.hotel.schemas import (  # noqa: E402
    FolioChargeCreate, FolioPaymentCreate, ReservationCreate, RoomCreate, RoomTypeCreate,
)
from src.apps.hotel.service import (  # noqa: E402
    FolioService, ReservationService, RoomService, RoomTypeService,
)
from src.apps.parking.infrastructure.models import (  # noqa: E402
    ParkingLocation, ParkingSpot, ParkingZone,
)
from src.apps.parking.sessions.models import ParkingSession  # noqa: E402
from src.core.database import async_session_factory, engine  # noqa: E402
from src.core.security import hash_password  # noqa: E402
from src.modules.accounting.schemas import JournalEntryLineCreate  # noqa: E402
from src.modules.accounting.seed import seed_chart_of_accounts  # noqa: E402
from src.modules.accounting.service import AccountingEngine  # noqa: E402

ORG_SLUG = "hotel-demo"
ORG_NAME = "Hotel Monterrey Center"
EMAIL = "admin@monterrey-center.com"
PASSWORD = "Monterrey1234!"
OLD_EMAIL = "admin@hotel-demo.com"

TYPES = [
    ("SEN", "Sencilla", 1, 90000, ["WiFi", "TV"]),
    ("DOB", "Doble", 2, 140000, ["WiFi", "TV", "Nevera"]),
    ("SUI", "Suite", 4, 260000, ["WiFi", "TV", "Nevera", "Jacuzzi"]),
]
ROOMS = [("101", "1", 0), ("102", "1", 0), ("103", "1", 0),
         ("104", "1", 1), ("201", "2", 1), ("202", "2", 1), ("203", "2", 1),
         ("301", "3", 2), ("302", "3", 2), ("303", "3", 2)]

# Huéspedes en casa (checked-in): (nombre, doc, tipo_idx, dias_desde_llegada, noches, adultos, niños)
IN_HOUSE = [
    ("Carlos Ramírez", "94123456", 1, 1, 3, 2, 0),
    ("Laura Méndez", "52987654", 2, 0, 4, 2, 1),
    ("Andrés Gil", "71456789", 1, 2, 3, 1, 0),
]
# Futuras (confirmadas)
FUTURE = [
    ("María Torres", "43112233", 0, 3, 2, 1, 0),
    ("Pedro Nieto", "80445566", 2, 6, 3, 2, 2),
]
# Parqueo ocupado ahora: (placa, tipo, hace_horas)
PARKED = [
    ("ABC123", "car", 5), ("XYZ789", "car", 3), ("MOT45D", "motorcycle", 1),
    ("DEF456", "car", 8), ("GHI012", "car", 2), ("JKL345", "car", 6),
]


async def _make(s, org, name, doc, tid, ci, co, adults, children):
    r = await ReservationService.create(s, org, ReservationCreate(
        guest_name=name, guest_document=doc, room_type_id=tid,
        check_in_date=ci, check_out_date=co, adults=adults, children=children))
    return uuid.UUID(str(r["id"]))


async def _checkin(s, org, rid):
    r = await s.get(HotelReservation, rid)
    free = await av.available_rooms(s, org, r.check_in_date, r.check_out_date, r.room_type_id, exclude_reservation_id=rid)
    if free:
        await ReservationService.check_in(s, org, rid, free[0].id)
        return free[0].id
    return None


async def main() -> None:
    print("=" * 70)
    print(f"Seed integral · {ORG_NAME}")
    print("=" * 70)
    today = date.today()

    async with async_session_factory() as s:
        # Migrar usuario previo si existe (evita duplicado)
        await s.execute(text("UPDATE public.users SET email=:new WHERE email=:old"),
                        {"new": EMAIL, "old": OLD_EMAIL})

        org = await s.scalar(text("SELECT id FROM organizations WHERE slug=:sl"), {"sl": ORG_SLUG})
        if not org:
            org = uuid.uuid4()
            await s.execute(text("INSERT INTO organizations (id,name,slug,type,settings,created_at,updated_at) "
                                 "VALUES (:i,:n,:sl,'business','{}'::jsonb,now(),now())"),
                            {"i": org, "n": ORG_NAME, "sl": ORG_SLUG})
        else:
            await s.execute(text("UPDATE organizations SET name=:n WHERE id=:i"), {"n": ORG_NAME, "i": org})

        uid = await s.scalar(text("SELECT id FROM public.users WHERE email=:e"), {"e": EMAIL})
        if not uid:
            uid = uuid.uuid4()
            await s.execute(text("INSERT INTO public.users (id,name,email,password_hash,created_at,updated_at) "
                                 "VALUES (:i,:n,:e,:p,now(),now())"),
                            {"i": uid, "n": "Recepción Monterrey", "e": EMAIL, "p": hash_password(PASSWORD)})
        else:
            await s.execute(text("UPDATE public.users SET password_hash=:p, name='Recepción Monterrey' WHERE id=:i"),
                            {"p": hash_password(PASSWORD), "i": uid})

        if not await s.scalar(text("SELECT 1 FROM memberships WHERE organization_id=:o AND user_id=:u"), {"o": org, "u": uid}):
            await s.execute(text("INSERT INTO memberships (id,organization_id,user_id,role,joined_at,created_at,updated_at) "
                                 "VALUES (:i,:o,:u,'owner',now(),now(),now())"), {"i": uuid.uuid4(), "o": org, "u": uid})

        # Activar apps: hotel, parking, accounting
        for code in ("hotel", "parking", "accounting"):
            app_id = await s.scalar(text("SELECT id FROM app_registry WHERE code=:c"), {"c": code})
            if app_id and not await s.scalar(text("SELECT 1 FROM organization_apps WHERE organization_id=:o AND app_id=:a"), {"o": org, "a": app_id}):
                await s.execute(text("INSERT INTO organization_apps (id,organization_id,app_id,status,activated_at,settings,created_at,updated_at) "
                                     "VALUES (:i,:o,:a,'active',now(),'{}'::jsonb,now(),now())"), {"i": uuid.uuid4(), "o": org, "a": app_id})
        print("  ✓ org + usuario owner + apps (hotel, parqueo, contabilidad)")

        # Reset datos demo de la org
        for t in ["hotel_folio_payments", "hotel_folio_charges", "hotel_folios",
                  "hotel_reservations", "hotel_rooms", "hotel_room_types",
                  "parking_sessions", "parking_spots", "parking_zones", "parking_locations"]:
            await s.execute(text(f"DELETE FROM {t} WHERE organization_id=:o"), {"o": org})
        # Contabilidad (journal_entry_lines no tiene org_id → vía subconsulta)
        await s.execute(text("DELETE FROM journal_entry_lines WHERE journal_entry_id IN "
                             "(SELECT id FROM journal_entries WHERE organization_id=:o)"), {"o": org})
        await s.execute(text("DELETE FROM journal_entries WHERE organization_id=:o"), {"o": org})
        await s.execute(text("DELETE FROM fiscal_periods WHERE organization_id=:o"), {"o": org})
        await s.execute(text("DELETE FROM chart_of_accounts WHERE organization_id=:o"), {"o": org})
        await s.commit()

        # -------- Hotel: tipos + habitaciones --------
        type_ids = []
        for code, name, cap, rate, am in TYPES:
            t = await RoomTypeService.create(s, org, RoomTypeCreate(code=code, name=name, capacity=cap, base_rate=rate, amenities=am))
            type_ids.append(t.id)
        for num, floor, ti in ROOMS:
            await RoomService.create(s, org, RoomCreate(room_type_id=type_ids[ti], number=num, floor=floor))
        await s.commit()

        # -------- Hotel: estadía pasada ya cerrada (PRIMERO, para no resetear
        # el estado físico de las habitaciones que luego ocuparán los de en casa) --------
        past_ci = today - timedelta(days=5)
        rid = await _make(s, org, "Sofía Ruiz", "39887766", type_ids[1], past_ci, past_ci + timedelta(days=3), 2, 0)
        await _checkin(s, org, rid)
        await FolioService.add_payment(s, org, rid, FolioPaymentCreate(amount=420000, method="cash"))
        await ReservationService.check_out(s, org, rid)
        await s.commit()

        # -------- Hotel: huéspedes en casa (check-in al final → quedan ocupadas) --------
        for i, (name, doc, ti, since, nights, ad, ch) in enumerate(IN_HOUSE):
            ci = today - timedelta(days=since)
            co = ci + timedelta(days=nights)
            rid = await _make(s, org, name, doc, type_ids[ti], ci, co, ad, ch)
            await _checkin(s, org, rid)
            if i == 0:  # uno con consumo + abono parcial
                await FolioService.add_charge(s, org, rid, FolioChargeCreate(description="Restaurante", quantity=1, unit_price=45000))
                await FolioService.add_payment(s, org, rid, FolioPaymentCreate(amount=200000, method="card"))
        await s.commit()

        # -------- Hotel: futuras confirmadas --------
        for name, doc, ti, since, nights, ad, ch in FUTURE:
            ci = today + timedelta(days=since)
            await _make(s, org, name, doc, type_ids[ti], ci, ci + timedelta(days=nights), ad, ch)
        await s.commit()
        print(f"  ✓ hotel: {len(TYPES)} tipos · {len(ROOMS)} habitaciones · {len(IN_HOUSE)} en casa · {len(FUTURE)} futuras · 1 cerrada")

        # -------- Parqueo: sede + zonas + celdas + sesiones ocupadas --------
        loc = ParkingLocation(organization_id=org, code="PARK-01", name="Parqueadero Monterrey",
                              city="Montería", total_capacity=20, current_occupancy=len(PARKED))
        s.add(loc); await s.flush()
        z1 = ParkingZone(organization_id=org, location_id=loc.id, name="Sótano 1", zone_type="general", level="B1", capacity=12)
        z2 = ParkingZone(organization_id=org, location_id=loc.id, name="Motos", zone_type="motorcycle", level="B1", capacity=8)
        s.add_all([z1, z2]); await s.flush()
        spots = []
        for n in range(1, 13):
            spots.append(ParkingSpot(organization_id=org, zone_id=z1.id, code=f"A-{n:03d}", spot_type="car"))
        for n in range(1, 9):
            spots.append(ParkingSpot(organization_id=org, zone_id=z2.id, code=f"M-{n:03d}", spot_type="motorcycle"))
        s.add_all(spots); await s.flush()
        # Ocupar spots con sesiones activas
        for i, (plate, vtype, hrs) in enumerate(PARKED):
            spot = spots[i] if vtype == "car" else spots[12 + i]
            spot.status = "occupied"
            s.add(ParkingSession(
                organization_id=org, location_id=loc.id, spot_id=spot.id, plate=plate,
                vehicle_type=vtype, entry_time=datetime.now(UTC) - timedelta(hours=hrs),
                status="active", payment_status="pending", entry_method="manual"))
        await s.commit()
        print(f"  ✓ parqueo: 1 sede · 2 zonas · {len(spots)} celdas · {len(PARKED)} ocupadas ahora")

        # -------- Contabilidad: catálogo + asientos --------
        await seed_chart_of_accounts(s, org, "church")
        await s.commit()
        await AccountingEngine.create_entry(
            s, org, today - timedelta(days=1), "Consignación en bancos", uid,
            [JournalEntryLineCreate(account_code="1.1.02", debit=Decimal("800000")),
             JournalEntryLineCreate(account_code="1.1.01", credit=Decimal("800000"))],
            source_app="hotel")
        await AccountingEngine.create_entry(
            s, org, today, "Recaudo de cartera", uid,
            [JournalEntryLineCreate(account_code="1.1.01", debit=Decimal("500000")),
             JournalEntryLineCreate(account_code="1.1.03", credit=Decimal("500000"))],
            source_app="hotel")
        await s.commit()
        print("  ✓ contabilidad: catálogo de cuentas + 2 asientos")

    print(f"\n✓ Listo. Login: {EMAIL} / {PASSWORD}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
