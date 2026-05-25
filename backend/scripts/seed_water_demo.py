"""Seed a complete SavvyWater demo: org + 100 subscribers + 3 months of
operations (lecturas, facturas, pagos, mora, PQRS).

Idempotent: each run wipes the water_* tables for the demo org and re-seeds
from scratch. The demo user + org membership are reused if they exist.

Usage:
    cd backend
    .venv/Scripts/python.exe scripts/seed_water_demo.py
"""

from __future__ import annotations

import asyncio
import logging
import random
import sys
import uuid
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

# Make `src.*` importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Windows consoles default to cp1252 — Spanish names crash print(); force UTF-8.
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

# Mute SQLAlchemy engine echo (it's set to True in dev mode by default)
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from src.apps.water.cartera.service import CarteraService  # noqa: E402
from src.apps.water.invoices.schemas import BatchGenerateRequest  # noqa: E402
from src.apps.water.invoices.service import InvoicesService  # noqa: E402
from src.apps.water.models import (  # noqa: E402
    WaterAuditLog,
    WaterCashAccount,
    WaterCashClosing,
    WaterConsumption,
    WaterInvoice,
    WaterMeter,
    WaterNotification,
    WaterPayment,
    WaterPaymentInvoice,
    WaterPqrs,
    WaterRoute,
    WaterRouteSubscriber,
    WaterSubscriber,
    WaterTariff,
    WaterTreasuryMovement,
)
from src.apps.water.payments.schemas import PaymentCreate  # noqa: E402
from src.apps.water.payments.service import PaymentsService  # noqa: E402
from src.core.database import async_session_factory, engine  # noqa: E402
from src.core.security import hash_password  # noqa: E402
from src.main import app  # noqa: E402, F401  # register all models
from src.modules.apps.models import AppRegistry, AppUserRole, OrganizationApp  # noqa: E402
from src.modules.auth.models import User  # noqa: E402
from src.modules.organization.models import Membership, Organization  # noqa: E402


# ---------------------------------------------------------------- Configuration

DEMO_EMAIL = "acueducto@demo.com"
DEMO_PASSWORD = "Demo1234!"
DEMO_NAME = "Administrador Acueducto Demo"
DEMO_ORG_SLUG = "acueducto-demo"
DEMO_ORG_NAME = "Acueducto Comunal Demo"

# Reference month for the demo: 3 months of billing ending at this period.
TODAY = date(2026, 5, 24)
LAST_PERIOD_YEAR = 2026
LAST_PERIOD_MONTH = 4  # we'll seed Feb, Mar, Apr

random.seed(42)


# ---------------------------------------------------------------- Static data

LAST_NAMES = [
    "Pérez", "González", "Rodríguez", "Martínez", "López", "Hernández",
    "García", "Ramírez", "Torres", "Sánchez", "Romero", "Castro", "Vargas",
    "Jiménez", "Moreno", "Ortiz", "Gutiérrez", "Ruiz", "Álvarez", "Mendoza",
    "Salazar", "Suárez", "Flores", "Vega", "Acosta", "Cárdenas",
]
FIRST_NAMES_M = [
    "Juan", "Luis", "Carlos", "Diego", "Jorge", "Andrés", "Miguel", "Felipe",
    "Sergio", "Iván", "Mauricio", "Esteban", "Daniel", "Javier", "Óscar",
    "Roberto", "Camilo", "Alejandro",
]
FIRST_NAMES_F = [
    "María", "Andrea", "Sofía", "Camila", "Daniela", "Valentina", "Laura",
    "Paola", "Diana", "Carolina", "Patricia", "Mónica", "Claudia", "Liliana",
    "Sandra", "Marcela", "Adriana",
]

NEIGHBORHOODS = [
    "Centro", "El Carmen", "La Esperanza", "San Rafael", "Las Flores",
    "Los Álamos", "Villa Hermosa", "El Bosque", "La Floresta",
    "Buenos Aires", "Santa Marta", "El Recreo",
]

COMMERCIAL_NAMES = [
    "Panadería La Espiga", "Tienda Don Carlos", "Ferretería El Tornillo",
    "Droguería Salud Plena", "Restaurante El Buen Sabor",
    "Variedades Caterine", "Pollos El Granjero", "Lavandería Limpia y Lista",
    "Heladería La Frutería", "Carnicería La Cosecha",
    "Papelería El Estudiante", "Cafetería Aroma", "Mecánica El Diesel",
    "Almacén Mil Estilos", "Tienda Mi Pueblito",
]

OFFICIAL_NAMES = [
    "Escuela Rural Antonio Nariño", "Centro de Salud San Pedro",
    "Alcaldía Municipal", "Inspección de Policía",
    "Casa de la Cultura", "Cancha Municipal", "Biblioteca Pública",
]

INDUSTRIAL_NAMES = [
    "Procesadora Lácteos del Sinú",
    "Aserradero El Pino",
    "Empacadora Tropical",
]

STREETS = ["Calle", "Carrera", "Diagonal", "Transversal"]
DOC_TYPES_PERSONAL = ["CC", "CC", "CC", "CE", "TI"]


def _random_name() -> tuple[str, str]:
    first = random.choice(FIRST_NAMES_M + FIRST_NAMES_F)
    last1 = random.choice(LAST_NAMES)
    last2 = random.choice(LAST_NAMES)
    return first, f"{last1} {last2}"


def _random_address() -> str:
    street = random.choice(STREETS)
    primary = random.randint(1, 60)
    secondary = random.randint(1, 80)
    number = random.randint(1, 99)
    return f"{street} {primary} # {secondary}-{number:02d}"


def _random_doc_number() -> str:
    return str(random.randint(10_000_000, 1_500_000_000))


def _random_mobile() -> str:
    return f"3{random.randint(0, 5)}{random.randint(10000000, 99999999)}"


# ---------------------------------------------------------------- DB helpers


async def _get_or_create_demo_user(db: AsyncSession) -> User:
    user = await db.scalar(select(User).where(User.email == DEMO_EMAIL))
    if user is None:
        user = User(
            id=uuid.uuid4(),
            name=DEMO_NAME,
            email=DEMO_EMAIL,
            password_hash=hash_password(DEMO_PASSWORD),
        )
        db.add(user)
        await db.flush()
        print(f"  + created demo user: {DEMO_EMAIL}")
    else:
        # Refresh password in case it changed
        user.password_hash = hash_password(DEMO_PASSWORD)
        print(f"  ~ reusing demo user: {DEMO_EMAIL} (password reset)")
    return user


async def _get_or_create_demo_org(db: AsyncSession) -> Organization:
    org = await db.scalar(
        select(Organization).where(Organization.slug == DEMO_ORG_SLUG)
    )
    if org is None:
        org = Organization(
            id=uuid.uuid4(),
            name=DEMO_ORG_NAME,
            slug=DEMO_ORG_SLUG,
            type="business",
            settings={"demo": True},
        )
        db.add(org)
        await db.flush()
        print(f"  + created demo org: {DEMO_ORG_NAME}")
    else:
        print(f"  ~ reusing demo org: {DEMO_ORG_NAME}")
    return org


async def _ensure_owner_membership(
    db: AsyncSession, user: User, org: Organization,
) -> None:
    existing = await db.scalar(
        select(Membership).where(
            Membership.organization_id == org.id,
            Membership.user_id == user.id,
        )
    )
    if existing is None:
        db.add(Membership(
            id=uuid.uuid4(),
            organization_id=org.id,
            user_id=user.id,
            role="owner",
        ))
        await db.flush()
        print(f"  + created owner membership")
    elif existing.role != "owner":
        existing.role = "owner"
        await db.flush()
        print(f"  ~ promoted membership to owner")


async def _ensure_water_app_enabled(
    db: AsyncSession, org: Organization,
) -> None:
    water_app = await db.scalar(
        select(AppRegistry).where(AppRegistry.code == "water")
    )
    if water_app is None:
        print("  ! WARN: water app not registered in app_registry — "
              "the user will need it activated to see the module")
        return
    existing = await db.scalar(
        select(OrganizationApp).where(
            OrganizationApp.organization_id == org.id,
            OrganizationApp.app_id == water_app.id,
        )
    )
    if existing is None:
        db.add(OrganizationApp(
            id=uuid.uuid4(),
            organization_id=org.id,
            app_id=water_app.id,
            status="active",
            activated_at=datetime.utcnow(),
        ))
        await db.flush()
        print(f"  + enabled water app on demo org")


async def _wipe_water_tables(db: AsyncSession, org_id: uuid.UUID) -> None:
    """Delete every water_* row for the demo org (child → parent order)."""
    # Children before parents — ondelete=CASCADE would do this but explicit is safer.
    for model in (
        WaterPaymentInvoice,
        WaterTreasuryMovement,
        WaterCashClosing,
        WaterPayment,
        WaterInvoice,
        WaterConsumption,
        WaterRouteSubscriber,
        WaterPqrs,
        WaterNotification,
        WaterAuditLog,
        WaterMeter,
        WaterSubscriber,
        WaterRoute,
        WaterCashAccount,
        WaterTariff,
    ):
        if hasattr(model, "organization_id"):
            await db.execute(
                delete(model).where(model.organization_id == org_id)
            )
        else:
            await db.execute(delete(model))  # association tables
    # WaterPaymentInvoice has no organization_id; delete by payment org
    await db.flush()
    print("  - wiped water_* tables for demo org")


# ---------------------------------------------------------------- Seed steps


async def _seed_tariffs(db: AsyncSession, org_id: uuid.UUID) -> list[WaterTariff]:
    """6 residential by estrato + commercial + industrial + official."""
    tariffs: list[WaterTariff] = []
    # Residential brackets: estrato 1 cheapest, 6 most expensive
    res_prices = {
        1: (2000, 1200, 1800),  # (fixed, basic price, surplus price)
        2: (3000, 1500, 2200),
        3: (5000, 2000, 3500),
        4: (8000, 2800, 4500),
        5: (12000, 3500, 5500),
        6: (18000, 4500, 7000),
    }
    for stratum, (fixed, basic_p, surplus_p) in res_prices.items():
        t = WaterTariff(
            id=uuid.uuid4(),
            organization_id=org_id,
            code=f"RES-E{stratum}",
            name=f"Residencial Estrato {stratum}",
            subscriber_type="residential",
            stratum=stratum,
            fixed_charge=Decimal(fixed),
            price_per_cubic=Decimal(basic_p),
            basic_limit_cubic=Decimal("20"),
            surplus_price_per_cubic=Decimal(surplus_p),
            reconnection_fee=Decimal("35000"),
            suspension_fee=Decimal("35000"),
            late_interest_rate=Decimal("0.02"),
            is_active=True,
            valid_from=date(2024, 1, 1),
        )
        db.add(t)
        tariffs.append(t)

    others = [
        ("commercial", "COM", "Comercial", 25000, 4500, 6000),
        ("industrial", "IND", "Industrial", 80000, 6500, 9000),
        ("official", "OFI", "Oficial", 15000, 3000, 4500),
    ]
    for sub_type, code, name, fixed, basic_p, surplus_p in others:
        t = WaterTariff(
            id=uuid.uuid4(),
            organization_id=org_id,
            code=code,
            name=name,
            subscriber_type=sub_type,
            stratum=None,
            fixed_charge=Decimal(fixed),
            price_per_cubic=Decimal(basic_p),
            basic_limit_cubic=Decimal("30"),
            surplus_price_per_cubic=Decimal(surplus_p),
            reconnection_fee=Decimal("50000"),
            suspension_fee=Decimal("50000"),
            late_interest_rate=Decimal("0.02"),
            is_active=True,
            valid_from=date(2024, 1, 1),
        )
        db.add(t)
        tariffs.append(t)
    await db.flush()
    print(f"  + seeded {len(tariffs)} tariffs (6 residential + 3 other)")
    return tariffs


async def _seed_subscribers_and_meters(
    db: AsyncSession, org_id: uuid.UUID,
) -> list[tuple[WaterSubscriber, WaterMeter]]:
    """100 subscribers (75 residential, 15 commercial, 7 official, 3 industrial)
    each with its own meter."""
    pairs: list[tuple[WaterSubscriber, WaterMeter]] = []

    # Residential x 75
    # Stratum distribution: 1->10, 2->20, 3->25, 4->10, 5->6, 6->4 = 75
    stratum_dist = [1] * 10 + [2] * 20 + [3] * 25 + [4] * 10 + [5] * 6 + [6] * 4
    random.shuffle(stratum_dist)
    for i, stratum in enumerate(stratum_dist, start=1):
        first, last = _random_name()
        sub = WaterSubscriber(
            id=uuid.uuid4(),
            organization_id=org_id,
            code=f"SUB-{i:04d}",
            document_type=random.choice(DOC_TYPES_PERSONAL),
            document_number=_random_doc_number(),
            first_name=first,
            last_name=last,
            business_name=None,
            email=None,
            mobile=_random_mobile(),
            address=_random_address(),
            neighborhood=random.choice(NEIGHBORHOODS),
            stratum=stratum,
            subscriber_type="residential",
            status="active",
            registered_at=date(2024, random.randint(1, 12), random.randint(1, 28)),
        )
        db.add(sub)
        pairs.append((sub, None))  # type: ignore[arg-type]

    # Commercial x 15
    base_idx = len(stratum_dist)
    for j, biz_name in enumerate(COMMERCIAL_NAMES, start=1):
        i = base_idx + j
        sub = WaterSubscriber(
            id=uuid.uuid4(),
            organization_id=org_id,
            code=f"SUB-{i:04d}",
            document_type="NIT",
            document_number=_random_doc_number(),
            first_name=biz_name.split()[0],  # placeholder
            last_name=None,
            business_name=biz_name,
            email=None,
            mobile=_random_mobile(),
            address=_random_address(),
            neighborhood=random.choice(NEIGHBORHOODS),
            stratum=None,
            subscriber_type="commercial",
            status="active",
            registered_at=date(2024, random.randint(1, 12), random.randint(1, 28)),
        )
        db.add(sub)
        pairs.append((sub, None))  # type: ignore[arg-type]

    # Official x 7
    base_idx = len(pairs)
    for j, off_name in enumerate(OFFICIAL_NAMES, start=1):
        i = base_idx + j
        sub = WaterSubscriber(
            id=uuid.uuid4(),
            organization_id=org_id,
            code=f"SUB-{i:04d}",
            document_type="NIT",
            document_number=_random_doc_number(),
            first_name=off_name.split()[0],
            last_name=None,
            business_name=off_name,
            email=None,
            mobile=None,
            address=_random_address(),
            neighborhood="Centro",
            stratum=None,
            subscriber_type="official",
            status="active",
            registered_at=date(2024, 1, 15),
        )
        db.add(sub)
        pairs.append((sub, None))  # type: ignore[arg-type]

    # Industrial x 3
    base_idx = len(pairs)
    for j, ind_name in enumerate(INDUSTRIAL_NAMES, start=1):
        i = base_idx + j
        sub = WaterSubscriber(
            id=uuid.uuid4(),
            organization_id=org_id,
            code=f"SUB-{i:04d}",
            document_type="NIT",
            document_number=_random_doc_number(),
            first_name=ind_name.split()[0],
            last_name=None,
            business_name=ind_name,
            email=None,
            mobile=_random_mobile(),
            address=_random_address(),
            neighborhood="Zona Industrial",
            stratum=None,
            subscriber_type="industrial",
            status="active",
            registered_at=date(2024, 3, 1),
        )
        db.add(sub)
        pairs.append((sub, None))  # type: ignore[arg-type]

    await db.flush()

    # Create one meter per subscriber
    final_pairs: list[tuple[WaterSubscriber, WaterMeter]] = []
    for idx, (sub, _) in enumerate(pairs, start=1):
        meter = WaterMeter(
            id=uuid.uuid4(),
            organization_id=org_id,
            subscriber_id=sub.id,
            serial_number=f"M-{idx:04d}",
            brand=random.choice(["Iusa", "Schlumberger", "Krohne", "Itron"]),
            diameter=random.choice(['1/2"', '3/4"', '1"']),
            install_date=sub.registered_at,
            initial_reading=Decimal("0"),
            last_reading=Decimal("0"),
            status="active",
        )
        db.add(meter)
        final_pairs.append((sub, meter))
    await db.flush()
    print(f"  + seeded {len(final_pairs)} subscribers + meters")
    return final_pairs


async def _seed_routes(
    db: AsyncSession, org_id: uuid.UUID,
    pairs: list[tuple[WaterSubscriber, WaterMeter]],
) -> None:
    """4 routes; assign subscribers round-robin-ish."""
    routes = []
    for code, name, count in [
        ("R-CEN", "Ruta Centro", 40),
        ("R-NOR", "Ruta Norte", 30),
        ("R-SUR", "Ruta Sur", 20),
        ("R-IND", "Ruta Industrial / Oficial", 10),
    ]:
        r = WaterRoute(
            id=uuid.uuid4(),
            organization_id=org_id,
            code=code,
            name=name,
            description=f"Ruta de lectura: {name}",
            is_active=True,
        )
        db.add(r)
        routes.append((r, count))
    await db.flush()

    cursor = 0
    for r, count in routes:
        for i in range(count):
            if cursor >= len(pairs):
                break
            sub, _ = pairs[cursor]
            db.add(WaterRouteSubscriber(
                id=uuid.uuid4(),
                organization_id=org_id,
                route_id=r.id,
                subscriber_id=sub.id,
                sort_order=i,
            ))
            cursor += 1
    await db.flush()
    print(f"  + seeded {len(routes)} routes with assignments")


async def _seed_cash_accounts(
    db: AsyncSession, org_id: uuid.UUID,
) -> WaterCashAccount:
    """2 cash accounts. Banco Bogotá is the default."""
    caja = WaterCashAccount(
        id=uuid.uuid4(),
        organization_id=org_id,
        code="CAJA",
        name="Caja Principal",
        type="cash",
        initial_balance=Decimal("200000"),
        is_default=False,
        is_active=True,
    )
    banco = WaterCashAccount(
        id=uuid.uuid4(),
        organization_id=org_id,
        code="BANK-001",
        name="Banco Bogotá",
        type="bank",
        initial_balance=Decimal("0"),
        is_default=True,
        is_active=True,
    )
    db.add_all([caja, banco])
    await db.flush()
    print("  + seeded 2 cash accounts (Banco Bogotá default)")
    return banco


async def _seed_consumptions_and_invoices(
    db: AsyncSession, org_id: uuid.UUID,
    pairs: list[tuple[WaterSubscriber, WaterMeter]],
) -> int:
    """3 months: Feb/Mar/Apr 2026. ~18 m³ ± 7 per subscriber per month."""
    invoice_count = 0
    for year, month in [(2026, 2), (2026, 3), (2026, 4)]:
        for sub, meter in pairs:
            # Industrial uses more, official a lot more
            if sub.subscriber_type == "industrial":
                base, stdev = 80, 25
            elif sub.subscriber_type == "official":
                base, stdev = 50, 20
            elif sub.subscriber_type == "commercial":
                base, stdev = 30, 12
            else:  # residential
                base, stdev = 18, 7
            cubic = max(1, int(random.gauss(base, stdev)))
            prev_reading = Decimal(meter.last_reading)
            new_reading = prev_reading + Decimal(cubic)

            c = WaterConsumption(
                id=uuid.uuid4(),
                organization_id=org_id,
                meter_id=meter.id,
                subscriber_id=sub.id,
                period_year=year,
                period_month=month,
                reading_date=date(year, month, random.randint(25, 28)),
                previous_reading=prev_reading,
                current_reading=new_reading,
                consumption_cubic=Decimal(cubic),
                is_estimated=False,
            )
            db.add(c)
            meter.last_reading = new_reading
            meter.last_reading_date = c.reading_date

        await db.flush()
        # Batch generate invoices for this period
        issue_day = random.randint(1, 5)
        issue_date = date(year, month + 1 if month < 12 else 1,
                          issue_day) if month < 12 else date(year + 1, 1, issue_day)
        result = await InvoicesService.batch_generate(
            db, org_id,
            BatchGenerateRequest(
                period_year=year, period_month=month,
                issue_date=issue_date,
                due_date=issue_date + timedelta(days=15),
            ),
        )
        invoice_count += result.generated

    print(f"  + seeded 3 months of consumptions + {invoice_count} invoices")
    return invoice_count


async def _seed_payments(
    db: AsyncSession, org_id: uuid.UUID,
    pairs: list[tuple[WaterSubscriber, WaterMeter]],
    cash_account: WaterCashAccount,
) -> int:
    """Pattern: 50% pay all invoices, 20% pay partial, 30% pay nothing.

    Pagos van con la fecha justa después de la emisión de la última factura.
    """
    paid_count = 0
    for sub, _ in pairs:
        bucket = random.random()
        # Sum all pending balance
        balance = await db.scalar(
            select(WaterInvoice.balance).where(
                WaterInvoice.organization_id == org_id,
                WaterInvoice.subscriber_id == sub.id,
                WaterInvoice.status != "annulled",
            )
        )
        # We need total pending — query sum
        from sqlalchemy import func
        total = await db.scalar(
            select(func.coalesce(func.sum(WaterInvoice.balance), 0)).where(
                WaterInvoice.organization_id == org_id,
                WaterInvoice.subscriber_id == sub.id,
                WaterInvoice.status.in_(("pending", "partial", "overdue")),
            )
        )
        total_pending = Decimal(total or 0)
        if total_pending <= 0:
            continue

        if bucket < 0.5:
            amount = total_pending  # full
        elif bucket < 0.7:
            amount = (total_pending * Decimal("0.5")).quantize(Decimal("0.01"))  # partial
        else:
            continue  # no payment

        await PaymentsService.register_payment(
            db, org_id,
            PaymentCreate(
                subscriber_id=sub.id,
                amount=amount,
                payment_date=date(2026, 5, random.randint(1, 20)),
                method=random.choice(["cash", "transfer", "transfer"]),
                cash_account_id=cash_account.id,
            ),
            collector_user_id=None,
        )
        paid_count += 1
    print(f"  + registered {paid_count} payments (rest left unpaid → cartera)")
    return paid_count


async def _recalc_cartera(db: AsyncSession, org_id: uuid.UUID) -> None:
    result = await CarteraService.recalc_overdue(db, org_id, on_date=TODAY)
    print(
        f"  + cartera recalculada: {result.invoices_marked_overdue} facturas "
        f"vencidas, {result.subscribers_marked_overdue} suscriptores en mora, "
        f"$ {result.total_interest_applied} en intereses",
    )


async def _seed_pqrs(
    db: AsyncSession, org_id: uuid.UUID,
    pairs: list[tuple[WaterSubscriber, WaterMeter]],
) -> None:
    subjects = [
        ("peticion", "Solicitud de revisión de medidor",
         "El medidor parece estar marcando consumo mayor al real."),
        ("queja", "Demora en respuesta",
         "Hace 15 días reporté un daño y nadie ha venido."),
        ("reclamo", "Cobro excesivo en factura",
         "La factura del mes pasado tiene un valor muy por encima de lo usual."),
        ("sugerencia", "Implementar pagos en línea",
         "Sería útil poder pagar sin tener que ir a la oficina."),
        ("queja", "Baja presión",
         "La presión del agua es muy baja en horas pico."),
        ("peticion", "Solicitar duplicado de factura",
         "Necesito el duplicado de la factura del periodo anterior."),
        ("reclamo", "Inconformidad con suspensión",
         "Me suspendieron el servicio sin previo aviso."),
        ("sugerencia", "Mejorar horario de atención",
         "El horario de atención al público es muy limitado."),
    ]
    statuses = ["open", "open", "in_progress", "in_progress", "resolved", "resolved", "closed", "open"]
    for i, ((tipo, subject, desc), status) in enumerate(zip(subjects, statuses, strict=False), start=1):
        sub, _ = random.choice(pairs[:75])  # residential pool
        db.add(WaterPqrs(
            id=uuid.uuid4(),
            organization_id=org_id,
            subscriber_id=sub.id,
            code=f"PQRS-{i:04d}",
            type=tipo,
            subject=subject,
            description=desc,
            status=status,
            response="Caso atendido satisfactoriamente." if status in ("resolved", "closed") else None,
            responded_at=datetime.utcnow() if status in ("resolved", "closed") else None,
        ))
    await db.flush()
    print(f"  + seeded 8 PQRS")


# ---------------------------------------------------------------- Entry point


async def main() -> None:
    print("=" * 70)
    print("SavvyWater · Seed Demo")
    print("=" * 70)

    async with async_session_factory() as session:
        try:
            print("\n[1/9] Demo user + org + access")
            user = await _get_or_create_demo_user(session)
            org = await _get_or_create_demo_org(session)
            await _ensure_owner_membership(session, user, org)
            await _ensure_water_app_enabled(session, org)

            print("\n[2/9] Wipe water_* tables for demo org")
            await _wipe_water_tables(session, org.id)

            print("\n[3/9] Tariffs")
            await _seed_tariffs(session, org.id)

            print("\n[4/9] Subscribers + meters")
            pairs = await _seed_subscribers_and_meters(session, org.id)

            print("\n[5/9] Routes")
            await _seed_routes(session, org.id, pairs)

            print("\n[6/9] Cash accounts")
            bank_account = await _seed_cash_accounts(session, org.id)

            print("\n[7/9] Consumptions + invoices (3 months)")
            invoice_count = await _seed_consumptions_and_invoices(session, org.id, pairs)

            print("\n[8/9] Payments (~70% pago, mezcla full/partial)")
            paid_count = await _seed_payments(session, org.id, pairs, bank_account)

            print("\n[9/9] Recalcular cartera + sembrar PQRS")
            await _recalc_cartera(session, org.id)
            await _seed_pqrs(session, org.id, pairs)

            await session.commit()

            # Final summary
            from sqlalchemy import func
            stats = await session.execute(
                select(
                    func.count(WaterInvoice.id),
                    func.sum(WaterInvoice.total),
                    func.sum(WaterInvoice.paid_amount),
                    func.sum(WaterInvoice.balance),
                )
                .where(WaterInvoice.organization_id == org.id)
            )
            n_inv, total_inv, paid, pending = stats.first()
            overdue_count = await session.scalar(
                select(func.count(WaterInvoice.id))
                .where(
                    WaterInvoice.organization_id == org.id,
                    WaterInvoice.status == "overdue",
                )
            )

            print("\n" + "=" * 70)
            print("DEMO LISTO")
            print("=" * 70)
            print(f"  Org:       {DEMO_ORG_NAME} (slug: {DEMO_ORG_SLUG})")
            print(f"  Login:     {DEMO_EMAIL}")
            print(f"  Password:  {DEMO_PASSWORD}")
            print()
            print(f"  100 suscriptores · {invoice_count} facturas en 3 meses")
            print(f"  $ {total_inv} facturado · $ {paid} pagado · $ {pending} pendiente")
            print(f"  {overdue_count} facturas en mora · {paid_count} pagos registrados")
            print("=" * 70)
        except Exception:
            await session.rollback()
            raise
        finally:
            await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
