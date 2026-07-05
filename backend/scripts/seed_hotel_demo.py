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
from src.apps.hr.models import HrContract, HrDepartment, HrEmployee, HrPosition  # noqa: E402
from src.apps.parking.infrastructure.models import (  # noqa: E402
    ParkingLocation, ParkingSpot, ParkingZone,
)
from src.apps.parking.sessions.models import ParkingSession  # noqa: E402
from src.core.database import async_session_factory, engine  # noqa: E402
from src.core.security import hash_password  # noqa: E402
from src.modules.accounting.schemas import JournalEntryLineCreate  # noqa: E402
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
# Salario mensual por cargo (COP). Auxilio de transporte para <= 2 SMMLV.
SALARY = {"GERE": 4500000, "CHEF": 2500000, "RECP": 1600000,
          "MESE": 1423500, "CAMA": 1423500, "AUXA": 1800000}
TRANSPORT = 200000

# Parqueo ya cobrado (vehículos que entraron y salieron): (placa, tipo, horas, total)
PARKED_DONE = [
    ("PQR111", "car", 2, 6000), ("STU222", "car", 3, 9000),
    ("VWX333", "motorcycle", 1, 1500), ("YZA444", "car", 5, 15000),
]

# Catálogo de cuentas HOTELERO (code, nombre, tipo, code_padre)
HOTEL_CHART = [
    ("1", "ACTIVOS", "asset", None),
    ("1.1", "Disponible", "asset", "1"),
    ("1.1.05", "Caja General", "asset", "1.1"),
    ("1.1.10", "Bancos", "asset", "1.1"),
    ("1.3", "Deudores", "asset", "1"),
    ("1.3.05", "Clientes", "asset", "1.3"),
    ("1.4", "Inventarios", "asset", "1"),
    ("1.4.05", "Inventario Restaurante", "asset", "1.4"),
    ("2", "PASIVOS", "liability", None),
    ("2.4", "Impuestos", "liability", "2"),
    ("2.4.05", "IVA por Pagar", "liability", "2.4"),
    ("2.5", "Obligaciones Laborales", "liability", "2"),
    ("2.5.05", "Salarios por Pagar", "liability", "2.5"),
    ("3", "PATRIMONIO", "equity", None),
    ("3.1.05", "Capital Social", "equity", "3"),
    ("4", "INGRESOS", "revenue", None),
    ("4.1", "Ingresos Operacionales", "revenue", "4"),
    ("4.1.05", "Ingresos Hospedaje", "revenue", "4.1"),
    ("4.1.10", "Ingresos Restaurante", "revenue", "4.1"),
    ("4.1.15", "Ingresos Parqueadero", "revenue", "4.1"),
    ("5", "GASTOS", "expense", None),
    ("5.1", "Gastos Operacionales", "expense", "5"),
    ("5.1.05", "Gastos de Personal", "expense", "5.1"),
    ("5.1.10", "Servicios Públicos", "expense", "5.1"),
    ("5.1.15", "Costo Insumos Restaurante", "expense", "5.1"),
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

        # Reset datos demo de la org (tablas hijas sin org_id → subconsulta)
        await s.execute(text("DELETE FROM pos_sale_lines WHERE sale_id IN "
                             "(SELECT id FROM pos_sales WHERE organization_id=:o)"), {"o": org})
        await s.execute(text("DELETE FROM hr_payroll_items WHERE payroll_id IN "
                             "(SELECT id FROM hr_payrolls WHERE organization_id=:o)"), {"o": org})
        for t in [
            # Hotel (hijas → padres)
            "hotel_folio_payments", "hotel_folio_charges", "hotel_folios",
            "hotel_reservations", "hotel_rooms", "hotel_room_types",
            # Parqueo (hijas → padres)
            "parking_service_orders", "parking_services", "parking_subscriptions",
            "parking_reservations", "parking_vehicles", "parking_pricing_rules",
            "parking_sessions", "parking_spots", "parking_zones", "parking_locations",
            # POS
            "pos_stock_movements", "pos_cash_registers", "pos_discounts", "pos_taxes",
            "pos_sales", "pos_inventory", "pos_products", "pos_categories", "pos_locations",
            # HR (hijas → padres)
            "hr_payrolls", "hr_payroll_periods", "hr_payroll_concepts",
            "hr_evaluations", "hr_evaluation_responses", "hr_evaluation_cycles",
            "hr_training_enrollments", "hr_training_courses",
            "hr_liquidation_items", "hr_liquidations",
            "hr_attendance", "hr_vacation_requests", "hr_vacation_balances", "hr_leaves",
            "hr_shifts", "hr_settings", "hr_employee_documents",
            "hr_contracts", "hr_employees", "hr_positions", "hr_departments",
        ]:
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
        # Ocupar spots con sesiones activas (vehículos parqueados ahora)
        for i, (plate, vtype, hrs) in enumerate(PARKED):
            spot = spots[i] if vtype == "car" else spots[12 + i]
            spot.status = "occupied"
            s.add(ParkingSession(
                organization_id=org, location_id=loc.id, spot_id=spot.id, plate=plate,
                vehicle_type=vtype, entry_time=datetime.now(UTC) - timedelta(hours=hrs),
                status="active", payment_status="pending", entry_method="manual"))
        # Sesiones ya cobradas (entraron y salieron) → ingreso realizado de parqueo
        for plate, vtype, dur, total in PARKED_DONE:
            entry = datetime.now(UTC) - timedelta(hours=dur + 1)
            s.add(ParkingSession(
                organization_id=org, location_id=loc.id, plate=plate, vehicle_type=vtype,
                entry_time=entry, exit_time=entry + timedelta(hours=dur), duration_minutes=dur * 60,
                amount=total, total=total, status="completed", payment_status="paid",
                payment_method="cash", entry_method="manual"))
        await s.commit()
        print(f"  ✓ parqueo: 1 sede · 2 zonas · {len(spots)} celdas · {len(PARKED)} ocupadas · {len(PARKED_DONE)} cobradas")

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

        # -------- HR: departamentos + cargos + personal + contratos --------
        dept_ids = {}
        for code, name in STAFF_DEPTS:
            d = HrDepartment(organization_id=org, code=code, name=name)
            s.add(d); await s.flush(); dept_ids[code] = d.id
        pos_ids = {}
        for code, name in STAFF_POS:
            p = HrPosition(organization_id=org, code=code, name=name)
            s.add(p); await s.flush(); pos_ids[code] = p.id
        payroll_total = 0
        for i, (fn, ln, doc, pcode, dcode) in enumerate(STAFF, 1):
            emp = HrEmployee(
                organization_id=org, employee_code=f"EMP-{i:03d}", first_name=fn, last_name=ln,
                document_type="CC", document_number=doc, hire_date=today - timedelta(days=200 + i * 15),
                department_id=dept_ids[dcode], position_id=pos_ids[pcode], status="active")
            s.add(emp); await s.flush()
            sal = SALARY[pcode]
            payroll_total += sal
            transp = TRANSPORT if sal <= 2 * 1423500 else 0
            s.add(HrContract(
                organization_id=org, employee_id=emp.id, contract_number=f"CTR-{i:03d}",
                contract_type="indefinido", start_date=emp.hire_date,
                base_salary=Decimal(str(sal)), transport_allowance=Decimal(str(transp)),
                payment_frequency="monthly", status="active"))
        await s.commit()
        print(f"  ✓ HR: {len(STAFF_DEPTS)} departamentos · {len(STAFF_POS)} cargos · "
              f"{len(STAFF)} empleados con contrato · nómina ${payroll_total:,}")

        # ===== HR submódulos (que ninguna vista quede vacía) =====
        async def ins(table, **cols):
            keys = ",".join(cols)
            ph = ",".join(f":{k}" for k in cols)
            await s.execute(text(f"INSERT INTO {table} ({keys}) VALUES ({ph})"), cols)

        emps = (await s.execute(text(
            "SELECT id, employee_code, first_name, coalesce(last_name,'') ln, position_id, hire_date "
            "FROM hr_employees WHERE organization_id=:o ORDER BY employee_code"), {"o": org})).all()
        id2code = {v: k for k, v in pos_ids.items()}

        # Turnos
        for code, name in [("TM", "Turno Mañana"), ("TT", "Turno Tarde"), ("TN", "Turno Noche")]:
            await ins("hr_shifts", id=uuid.uuid4(), organization_id=org, code=code, name=name)

        # Asistencia (últimos 3 días hábiles, todos presentes)
        for emp in emps:
            for dd in range(1, 4):
                await ins("hr_attendance", id=uuid.uuid4(), organization_id=org,
                          employee_id=emp.id, work_date=today - timedelta(days=dd), status="present")

        # Vacaciones: saldo por empleado + un par de solicitudes
        for emp in emps:
            await ins("hr_vacation_balances", id=uuid.uuid4(), organization_id=org,
                      employee_id=emp.id, period_year=today.year)
        await ins("hr_vacation_requests", id=uuid.uuid4(), organization_id=org, employee_id=emps[1].id,
                  request_number="VAC-001", start_date=today + timedelta(days=10),
                  end_date=today + timedelta(days=17), days_count=Decimal("7"), status="approved")
        await ins("hr_vacation_requests", id=uuid.uuid4(), organization_id=org, employee_id=emps[4].id,
                  request_number="VAC-002", start_date=today + timedelta(days=20),
                  end_date=today + timedelta(days=25), days_count=Decimal("5"), status="pending")

        # Incapacidades
        await ins("hr_leaves", id=uuid.uuid4(), organization_id=org, employee_id=emps[5].id,
                  leave_number="INC-001", leave_type="medical", start_date=today - timedelta(days=8),
                  end_date=today - timedelta(days=6), days_count=Decimal("3"), status="completed")

        # Nómina: conceptos
        for code, name, ctype, cat in [
            ("SAL", "Salario básico", "earning", "salary"),
            ("AUXT", "Auxilio de transporte", "earning", "allowance"),
            ("HEX", "Horas extra", "earning", "overtime"),
            ("SALUD", "Salud (4%)", "deduction", "health"),
            ("PENS", "Pensión (4%)", "deduction", "pension"),
            ("RTF", "Retención en la fuente", "deduction", "tax"),
        ]:
            await ins("hr_payroll_concepts", id=uuid.uuid4(), organization_id=org,
                      code=code, name=name, concept_type=ctype, category=cat)

        # Nómina: período pasado (pagado) + corrida por empleado
        period_id = uuid.uuid4()
        await ins("hr_payroll_periods", id=period_id, organization_id=org, code="2026-06-Q2",
                  name="Segunda quincena junio 2026", start_date=today.replace(day=16) - timedelta(days=30),
                  end_date=today.replace(day=1) - timedelta(days=1), status="approved")
        for emp in emps:
            sal = SALARY[id2code[emp.position_id]]
            quincena = round(sal / 2)
            salud = round(quincena * 0.04)
            pens = round(quincena * 0.04)
            pid = uuid.uuid4()
            await ins("hr_payrolls", id=pid, organization_id=org, period_id=period_id,
                      employee_id=emp.id, employee_code=emp.employee_code,
                      employee_name=f"{emp.first_name} {emp.ln}".strip())
            await ins("hr_payroll_items", id=uuid.uuid4(), payroll_id=pid, concept_code="SAL",
                      concept_name="Salario básico", concept_type="earning", amount=Decimal(str(quincena)))
            await ins("hr_payroll_items", id=uuid.uuid4(), payroll_id=pid, concept_code="SALUD",
                      concept_name="Salud (4%)", concept_type="deduction", amount=Decimal(str(salud)))
            await ins("hr_payroll_items", id=uuid.uuid4(), payroll_id=pid, concept_code="PENS",
                      concept_name="Pensión (4%)", concept_type="deduction", amount=Decimal(str(pens)))

        # Evaluaciones: ciclo + una por empleado
        cycle_id = uuid.uuid4()
        await ins("hr_evaluation_cycles", id=cycle_id, organization_id=org, code="EVAL-2026",
                  name="Evaluación de desempeño 2026", start_date=today.replace(month=1, day=1),
                  end_date=today.replace(month=12, day=31))
        for emp in emps:
            await ins("hr_evaluations", id=uuid.uuid4(), organization_id=org,
                      cycle_id=cycle_id, employee_id=emp.id)

        # Capacitaciones: cursos + inscripciones
        courses = {}
        for code, name in [("IND", "Inducción hotelera"), ("SST", "Seguridad y salud en el trabajo"),
                           ("SERV", "Servicio al cliente")]:
            cid = uuid.uuid4(); courses[code] = cid
            await ins("hr_training_courses", id=cid, organization_id=org, code=code, name=name)
        for i, emp in enumerate(emps):
            await ins("hr_training_enrollments", id=uuid.uuid4(), organization_id=org,
                      course_id=courses["IND"], employee_id=emp.id)
            if i % 2 == 0:
                await ins("hr_training_enrollments", id=uuid.uuid4(), organization_id=org,
                          course_id=courses["SERV"], employee_id=emp.id)

        # Documentos por empleado
        for emp in emps:
            await ins("hr_employee_documents", id=uuid.uuid4(), organization_id=org,
                      employee_id=emp.id, document_type="contract", title="Contrato de trabajo")

        # Liquidación: un ex-empleado terminado
        ex_id = uuid.uuid4()
        ex_start = today - timedelta(days=730)
        ex_end = today - timedelta(days=30)
        await ins("hr_employees", id=ex_id, organization_id=org, employee_code="EMP-009",
                  first_name="Diego", last_name="Ortiz", document_type="CC", document_number="99001122",
                  hire_date=ex_start, department_id=dept_ids["RES"], position_id=pos_ids["MESE"],
                  status="terminated")
        liq_id = uuid.uuid4()
        await ins("hr_liquidations", id=liq_id, organization_id=org, employee_id=ex_id,
                  liquidation_number="LIQ-001", termination_date=ex_end, termination_reason="voluntary",
                  last_worked_date=ex_end, contract_start_date=ex_start)
        for cc, cn, kind, amt in [
            ("cesantias", "Cesantías", "earning", 1423500),
            ("intereses_cesantias", "Intereses sobre cesantías", "earning", 170820),
            ("prima_servicios", "Prima de servicios", "earning", 711750),
            ("vacaciones", "Vacaciones", "earning", 593125),
        ]:
            await ins("hr_liquidation_items", id=uuid.uuid4(), organization_id=org, liquidation_id=liq_id,
                      concept_code=cc, concept_name=cn, kind=kind, amount=Decimal(str(amt)))

        # Settings
        await ins("hr_settings", id=uuid.uuid4(), organization_id=org)
        await s.commit()
        print("  ✓ HR submódulos: turnos, asistencia, vacaciones, incapacidades, nómina "
              "(período+corridas), evaluaciones, capacitaciones, liquidación, documentos, settings")

        # ===== Parqueo submódulos =====
        for plate, _v, _h in PARKED:
            await ins("parking_vehicles", id=uuid.uuid4(), organization_id=org, plate=plate)
        for plate, _v, _d, _t in PARKED_DONE:
            await ins("parking_vehicles", id=uuid.uuid4(), organization_id=org, plate=plate)
        for name, price in [("Carro por hora", 3000), ("Moto por hora", 1500), ("Día completo carro", 20000)]:
            await ins("parking_pricing_rules", id=uuid.uuid4(), organization_id=org, name=name)
        svc_ids = {}
        for name, price in [("Lavado sencillo", 15000), ("Lavado completo", 25000), ("Encerado", 40000)]:
            sid = uuid.uuid4(); svc_ids[name] = (sid, price)
            await ins("parking_services", id=sid, organization_id=org, name=name)
        for name in ("Lavado sencillo", "Lavado completo"):
            sid, price = svc_ids[name]
            await ins("parking_service_orders", id=uuid.uuid4(), organization_id=org,
                      service_id=sid, price=Decimal(str(price)))
        for name, price in [("Mensualidad carro", 150000), ("Mensualidad moto", 80000)]:
            await ins("parking_subscriptions", id=uuid.uuid4(), organization_id=org,
                      name=name, price=Decimal(str(price)))
        for d in (1, 2):
            frm = datetime.now(UTC) + timedelta(days=d, hours=8)
            await ins("parking_reservations", id=uuid.uuid4(), organization_id=org, location_id=loc.id,
                      reserved_from=frm, reserved_until=frm + timedelta(hours=6))
        await s.commit()
        print("  ✓ Parqueo submódulos: vehículos, tarifas, servicios+órdenes, suscripciones, reservas")

        # ===== POS submódulos =====
        for name in ("Caja 1", "Caja 2"):
            await ins("pos_cash_registers", id=uuid.uuid4(), organization_id=org,
                      location_id=loc_id, register_name=name)
        for code, name, rate in [("IVA19", "IVA 19%", Decimal("0.19")), ("EXENTO", "Exento", Decimal("0"))]:
            await ins("pos_taxes", id=uuid.uuid4(), organization_id=org, code=code, name=name, rate=rate)
        for code, name, value in [("PROMO10", "Promoción 10%", Decimal("10")), ("EMPL", "Descuento empleado", Decimal("15"))]:
            await ins("pos_discounts", id=uuid.uuid4(), organization_id=org, code=code, name=name, value=value)
        for sku, (pid, name, price) in prod_ids.items():
            await ins("pos_stock_movements", id=uuid.uuid4(), organization_id=org, product_id=pid,
                      location_id=loc_id, movement_type="in", quantity=Decimal("50"))
        await s.commit()
        print("  ✓ POS submódulos: cajas, impuestos, descuentos, movimientos de stock")

        # -------- Contabilidad: catálogo hotelero + asientos que RESUMEN lo real --------
        code_id = {}
        for code, name, atype, parent in HOTEL_CHART:
            aid = uuid.uuid4(); code_id[code] = aid
            await s.execute(text(
                "INSERT INTO chart_of_accounts (id,organization_id,code,name,type,parent_id,is_active,is_system,created_at,updated_at) "
                "VALUES (:i,:o,:c,:n,:t,:p,true,false,now(),now())"),
                {"i": aid, "o": org, "c": code, "n": name, "t": atype,
                 "p": code_id.get(parent) if parent else None})
        await s.commit()

        # Totales reales de las otras apps
        hospedaje = float(await s.scalar(text("SELECT coalesce(sum(amount),0) FROM hotel_folio_payments WHERE organization_id=:o"), {"o": org}))
        restaurante = float(await s.scalar(text("SELECT coalesce(sum(total),0) FROM pos_sales WHERE organization_id=:o AND status='completed' AND payment_method='cash'"), {"o": org}))
        parqueo = float(await s.scalar(text("SELECT coalesce(sum(total),0) FROM parking_sessions WHERE organization_id=:o AND status='completed'"), {"o": org}))
        nomina = float(payroll_total)
        insumos = round(restaurante * 0.4)

        async def _entry(desc, debit_code, credit_code, amount):
            if amount <= 0:
                return
            await AccountingEngine.create_entry(
                s, org, today, desc, uid,
                [JournalEntryLineCreate(account_code=debit_code, debit=Decimal(str(amount))),
                 JournalEntryLineCreate(account_code=credit_code, credit=Decimal(str(amount)))],
                source_app="hotel")

        await _entry("Ingresos de hospedaje", "1.1.05", "4.1.05", hospedaje)
        await _entry("Ingresos del restaurante", "1.1.05", "4.1.10", restaurante)
        await _entry("Ingresos de parqueadero", "1.1.05", "4.1.15", parqueo)
        await _entry("Nómina del personal", "5.1.05", "1.1.10", nomina)
        await _entry("Compra de insumos del restaurante", "1.4.05", "1.1.05", insumos)
        await s.commit()
        print(f"  ✓ contabilidad: catálogo hotelero ({len(HOTEL_CHART)} cuentas) + asientos "
              f"(hospedaje ${hospedaje:,.0f} · restaurante ${restaurante:,.0f} · parqueo ${parqueo:,.0f} · nómina ${nomina:,.0f})")

    print(f"\n✓ Listo. Login: {EMAIL} / {PASSWORD}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
