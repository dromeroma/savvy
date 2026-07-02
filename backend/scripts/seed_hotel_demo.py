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
from src.apps.hr.models import HrDepartment, HrEmployee, HrPosition  # noqa: E402
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

# POS restaurante: categorías y productos (sku, nombre, cat, costo, precio, stock, min)
RES_CATS = [("PLA", "Platos fuertes"), ("BEB", "Bebidas"), ("POS", "Postres")]
RES_PRODUCTS = [
    ("PLA-01", "Bandeja Paisa", "PLA", 15000, 32000, 40, 10),
    ("PLA-02", "Mojarra Frita", "PLA", 18000, 38000, 25, 8),
    ("PLA-03", "Pechuga a la Plancha", "PLA", 12000, 26000, 30, 10),
    ("BEB-01", "Gaseosa", "BEB", 2000, 5000, 80, 20),
    ("BEB-02", "Jugo Natural", "BEB", 3000, 8000, 50, 15),
    ("BEB-03", "Cerveza", "BEB", 3000, 7000, 60, 20),
    ("POS-01", "Flan de Caramelo", "POS", 3000, 9000, 20, 6),
    ("POS-02", "Helado", "POS", 2500, 7000, 24, 6),
]

# HR personal del hotel: (nombre, apellido, doc, cargo_code, depto_code)
STAFF_DEPTS = [("REC", "Recepción"), ("RES", "Restaurante"), ("HSK", "Housekeeping"), ("ADM", "Administración")]
STAFF_POS = [("GERE", "Gerente"), ("RECP", "Recepcionista"), ("CHEF", "Chef"),
             ("MESE", "Mesero"), ("CAMA", "Camarera"), ("AUXA", "Auxiliar Administrativo")]
STAFF = [
    ("Juan", "Ríos", "10111222", "GERE", "ADM"),
    ("Marta", "López", "22333444", "RECP", "REC"),
    ("Luis", "Peña", "33444555", "RECP", "REC"),
    ("Carlos", "Mesa", "44555666", "CHEF", "RES"),
    ("Ana", "Díaz", "55666777", "MESE", "RES"),
    ("Rosa", "Vega", "66777888", "CAMA", "HSK"),
    ("Elena", "Mora", "77888999", "CAMA", "HSK"),
    ("Pedro", "Sanz", "88999000", "AUXA", "ADM"),
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

        # Activar apps: hotel, parking, accounting, pos, hr
        for code in ("hotel", "parking", "accounting", "pos", "hr"):
            app_id = await s.scalar(text("SELECT id FROM app_registry WHERE code=:c"), {"c": code})
            if app_id and not await s.scalar(text("SELECT 1 FROM organization_apps WHERE organization_id=:o AND app_id=:a"), {"o": org, "a": app_id}):
                await s.execute(text("INSERT INTO organization_apps (id,organization_id,app_id,status,activated_at,settings,created_at,updated_at) "
                                     "VALUES (:i,:o,:a,'active',now(),'{}'::jsonb,now(),now())"), {"i": uuid.uuid4(), "o": org, "a": app_id})
        print("  ✓ org + usuario owner + apps (hotel, parqueo, contabilidad, POS, HR)")

        # Reset datos demo de la org
        # pos_sale_lines no tiene org_id → subconsulta
        await s.execute(text("DELETE FROM pos_sale_lines WHERE sale_id IN "
                             "(SELECT id FROM pos_sales WHERE organization_id=:o)"), {"o": org})
        for t in ["hotel_folio_payments", "hotel_folio_charges", "hotel_folios",
                  "hotel_reservations", "hotel_rooms", "hotel_room_types",
                  "parking_sessions", "parking_spots", "parking_zones", "parking_locations",
                  "pos_sales", "pos_inventory", "pos_products", "pos_categories", "pos_locations",
                  "hr_employees", "hr_positions", "hr_departments"]:
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
        carlos_rid = None
        for i, (name, doc, ti, since, nights, ad, ch) in enumerate(IN_HOUSE):
            ci = today - timedelta(days=since)
            co = ci + timedelta(days=nights)
            rid = await _make(s, org, name, doc, type_ids[ti], ci, co, ad, ch)
            await _checkin(s, org, rid)
            if i == 0:  # Carlos: abono parcial (su consumo POS se carga luego)
                carlos_rid = rid
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

        # -------- POS restaurante: sede + carta + inventario + ventas --------
        loc_id = uuid.uuid4()
        await s.execute(text("INSERT INTO pos_locations (id,organization_id,code,name,status,created_at,updated_at) "
                             "VALUES (:i,:o,'REST','Restaurante Monterrey','active',now(),now())"), {"i": loc_id, "o": org})
        cat_ids = {}
        for code, name in RES_CATS:
            cid = uuid.uuid4(); cat_ids[code] = cid
            await s.execute(text("INSERT INTO pos_categories (id,organization_id,code,name,sort_order,status,created_at,updated_at) "
                                 "VALUES (:i,:o,:c,:n,0,'active',now(),now())"), {"i": cid, "o": org, "c": code, "n": name})
        prod_ids = {}
        for sku, name, cat, cost, price, stock, minst in RES_PRODUCTS:
            pid = uuid.uuid4(); prod_ids[sku] = (pid, name, price)
            await s.execute(text("INSERT INTO pos_products (id,organization_id,category_id,sku,name,product_type,price,cost,tracks_inventory,attributes,status,created_at,updated_at) "
                                 "VALUES (:i,:o,:cat,:sku,:n,'simple',:p,:c,true,'{}'::jsonb,'active',now(),now())"),
                            {"i": pid, "o": org, "cat": cat_ids[cat], "sku": sku, "n": name, "p": price, "c": cost})
            await s.execute(text("INSERT INTO pos_inventory (id,organization_id,product_id,location_id,quantity,min_stock,created_at,updated_at) "
                                 "VALUES (:i,:o,:pid,:loc,:q,:m,now(),now())"),
                            {"i": uuid.uuid4(), "o": org, "pid": pid, "loc": loc_id, "q": stock, "m": minst})
        # unas ventas de días recientes
        import random as _rnd
        _rnd.seed(11)
        skus = list(prod_ids)
        n_sales = 0
        for day in range(7, 0, -1):
            when = datetime.now(UTC) - timedelta(days=day, hours=3)
            chosen = _rnd.sample(skus, 3)
            sid = uuid.uuid4()
            sub = sum(prod_ids[k][2] for k in chosen)
            await s.execute(text("INSERT INTO pos_sales (id,organization_id,sale_number,location_id,subtotal,discount_amount,tax_amount,total,payment_method,payment_details,status,created_at,updated_at) "
                                 "VALUES (:i,:o,:num,:loc,:sub,0,0,:sub,'cash','{}'::jsonb,'completed',:ts,:ts)"),
                            {"i": sid, "o": org, "num": f"R-{when:%Y%m%d}-{day}", "loc": loc_id, "sub": sub, "ts": when})
            for k in chosen:
                pid, name, price = prod_ids[k]
                await s.execute(text("INSERT INTO pos_sale_lines (id,sale_id,product_id,product_name,sku,quantity,unit_price,discount,tax_rate,tax_amount,line_total,created_at,updated_at) "
                                     "VALUES (:i,:sid,:pid,:n,:sku,1,:p,0,0,0,:p,:ts,:ts)"),
                                {"i": uuid.uuid4(), "sid": sid, "pid": pid, "n": name, "sku": k, "p": price, "ts": when})
            n_sales += 1
        # venta de HOY que se carga al folio de Carlos (integración POS→habitación)
        sale_today = uuid.uuid4()
        combo = [prod_ids["PLA-01"], prod_ids["BEB-03"], prod_ids["POS-01"]]
        subt = sum(c[2] for c in combo)
        await s.execute(text("INSERT INTO pos_sales (id,organization_id,sale_number,location_id,subtotal,discount_amount,tax_amount,total,payment_method,payment_details,status,created_at,updated_at) "
                             "VALUES (:i,:o,:num,:loc,:sub,0,0,:sub,'credit','{}'::jsonb,'completed',now(),now())"),
                        {"i": sale_today, "o": org, "num": "R-HOY-CARLOS", "loc": loc_id, "sub": subt})
        for pid, name, price in combo:
            await s.execute(text("INSERT INTO pos_sale_lines (id,sale_id,product_id,product_name,sku,quantity,unit_price,discount,tax_rate,tax_amount,line_total,created_at,updated_at) "
                                 "VALUES (:i,:sid,:pid,:n,'',1,:p,0,0,0,:p,now(),now())"),
                            {"i": uuid.uuid4(), "sid": sale_today, "pid": pid, "n": name, "p": price})
        await s.commit()
        if carlos_rid:
            await FolioService.charge_from_pos(s, org, carlos_rid, sale_today)
            await s.commit()
        print(f"  ✓ POS restaurante: {len(RES_PRODUCTS)} platos · {n_sales+1} ventas (1 cargada a la habitación de Carlos)")

        # -------- HR: departamentos + cargos + personal --------
        dept_ids = {}
        for code, name in STAFF_DEPTS:
            d = HrDepartment(organization_id=org, code=code, name=name)
            s.add(d); await s.flush(); dept_ids[code] = d.id
        pos_ids = {}
        for code, name in STAFF_POS:
            p = HrPosition(organization_id=org, code=code, name=name)
            s.add(p); await s.flush(); pos_ids[code] = p.id
        for i, (fn, ln, doc, pcode, dcode) in enumerate(STAFF, 1):
            s.add(HrEmployee(
                organization_id=org, employee_code=f"EMP-{i:03d}", first_name=fn, last_name=ln,
                document_type="CC", document_number=doc, hire_date=today - timedelta(days=200 + i * 15),
                department_id=dept_ids[dcode], position_id=pos_ids[pcode], status="active"))
        await s.commit()
        print(f"  ✓ HR: {len(STAFF_DEPTS)} departamentos · {len(STAFF_POS)} cargos · {len(STAFF)} empleados")

    print(f"\n✓ Listo. Login: {EMAIL} / {PASSWORD}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
