"""Seed demo completo de SavvyMemorial: una funeraria con 100 contratos,
cuotas históricas, pagos, mora, 5 servicios funerarios, leads CRM,
empleados con asistencia y reportes alimentados con datos reales.

Idempotente: borra y vuelve a crear toda la data memorial_* para la org demo.

Uso:
    cd backend
    .venv/Scripts/python.exe scripts/seed_memorial_demo.py
"""

from __future__ import annotations

import asyncio
import logging
import random
import sys
import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import delete, select  # noqa: E402
from sqlalchemy.ext.asyncio import AsyncSession  # noqa: E402

from src.apps.memorial.contracts.schemas import (  # noqa: E402
    BeneficiaryCreate,
    ContractCreate,
)
from src.apps.memorial.contracts.service import ContractsService  # noqa: E402
from src.apps.memorial.crm.schemas import LeadCreate  # noqa: E402
from src.apps.memorial.crm.service import LeadsService  # noqa: E402
from src.apps.memorial.invoices.schemas import BatchGenerateRequest  # noqa: E402
from src.apps.memorial.invoices.service import InvoicesService  # noqa: E402
from src.apps.memorial.models import (  # noqa: E402
    MemorialAttendance,
    MemorialAuditLog,
    MemorialDriver,
    MemorialEmployee,
    MemorialExequialBeneficiary,
    MemorialExequialContract,
    MemorialExequialPlan,
    MemorialInventoryItem,
    MemorialInventoryMovement,
    MemorialInvoice,
    MemorialLead,
    MemorialLeadCommunication,
    MemorialLocation,
    MemorialOven,
    MemorialPayment,
    MemorialPaymentInvoice,
    MemorialPosition,
    MemorialRoom,
    MemorialService,
    MemorialServiceEvent,
    MemorialServiceFamily,
    MemorialTransfer,
    MemorialVehicle,
)
from src.apps.memorial.payments.schemas import PaymentCreate  # noqa: E402
from src.apps.memorial.payments.service import PaymentsService  # noqa: E402
from src.apps.memorial.plans.schemas import PlanCreate  # noqa: E402
from src.apps.memorial.plans.service import PlansService  # noqa: E402
from src.core.database import async_session_factory, engine  # noqa: E402
from src.core.security import hash_password  # noqa: E402
from src.main import app  # noqa: E402, F401  # carga todos los modelos
from src.modules.apps.models import AppRegistry, OrganizationApp  # noqa: E402
from src.modules.auth.models import User  # noqa: E402
from src.modules.organization.models import Membership, Organization  # noqa: E402


# ---------------------------------------------------------------- Configuración

DEMO_EMAIL = "admin@memorial-demo.com"
DEMO_PASSWORD = "Memorial2026*"
DEMO_NAME = "Administrador Funeraria San Rafael"
DEMO_ORG_SLUG = "memorial-demo"
DEMO_ORG_NAME = "Funeraria San Rafael"

TODAY = date(2026, 5, 27)

# Reproducible
random.seed(42)


# ---------------------------------------------------------------- Datos estáticos

LAST_NAMES = [
    "Pérez", "González", "Rodríguez", "Martínez", "López", "Hernández",
    "García", "Ramírez", "Torres", "Sánchez", "Romero", "Castro", "Vargas",
    "Jiménez", "Moreno", "Ortiz", "Gutiérrez", "Ruiz", "Álvarez", "Mendoza",
    "Salazar", "Suárez", "Flores", "Vega", "Acosta", "Cárdenas", "Castaño",
    "Bedoya", "Restrepo", "Quintero", "Ospina", "Cano", "Henao", "Giraldo",
    "Arango", "Bermúdez", "Marín", "Rivera", "Ávila", "Pulido",
]
FIRST_NAMES_M = [
    "Juan", "Luis", "Carlos", "Diego", "Jorge", "Andrés", "Miguel", "Felipe",
    "Sergio", "Iván", "Mauricio", "Esteban", "Daniel", "Javier", "Óscar",
    "Roberto", "Camilo", "Alejandro", "Pedro", "Hernán", "Francisco",
]
FIRST_NAMES_F = [
    "María", "Andrea", "Sofía", "Camila", "Daniela", "Valentina", "Laura",
    "Paola", "Diana", "Carolina", "Patricia", "Mónica", "Claudia", "Liliana",
    "Sandra", "Marcela", "Adriana", "Beatriz", "Gloria", "Esperanza",
]
RELATIONSHIPS = ["Cónyuge", "Hijo(a)", "Padre", "Madre", "Hermano(a)", "Tío(a)"]
DOC_TYPES = ["CC", "CC", "CC", "CE", "TI"]
NEIGHBORHOODS = [
    "Centro", "El Carmen", "La Esperanza", "San Rafael", "Las Flores",
    "Los Álamos", "Villa Hermosa", "El Bosque", "La Floresta", "Buenos Aires",
]
STREETS = ["Calle", "Carrera", "Diagonal", "Transversal"]


# Casos de portal documentados que se muestran al usuario al final.
SAMPLE_PORTAL_CASES = [
    {
        "key": "al_dia_familiar",
        "first_name": "María",
        "last_name": "Pérez Castaño",
        "email": "maria.perez@demo.com",
        "document_type": "CC",
        "document_number": "1001001",
        "mobile": "3001001001",
        "address": "Calle 12 # 34-56",
        "plan_kind": "premium",
        "affiliate_type": "familiar",
        "scenario": "al_dia",
        "label": "Al día · plan Premium familiar (3 beneficiarios)",
    },
    {
        "key": "mora_leve",
        "first_name": "Carlos",
        "last_name": "Ramírez López",
        "email": "carlos.ramirez@demo.com",
        "document_type": "CC",
        "document_number": "1001002",
        "mobile": "3001001002",
        "address": "Carrera 8 # 20-15",
        "plan_kind": "estandar",
        "affiliate_type": "individual",
        "scenario": "mora_leve",
        "label": "Mora leve · 1 cuota vencida",
    },
    {
        "key": "mora_fuerte",
        "first_name": "Ana",
        "last_name": "López Bedoya",
        "email": "ana.lopez@demo.com",
        "document_type": "CC",
        "document_number": "1001003",
        "mobile": "3001001003",
        "address": "Diagonal 5 # 12-08",
        "plan_kind": "economico",
        "affiliate_type": "familiar",
        "scenario": "mora_fuerte",
        "label": "Mora fuerte · 4 cuotas vencidas",
    },
    {
        "key": "con_servicio",
        "first_name": "Jorge",
        "last_name": "Castaño Henao",
        "email": "jorge.castano@demo.com",
        "document_type": "CC",
        "document_number": "1001004",
        "mobile": "3001001004",
        "address": "Transversal 10 # 45-23",
        "plan_kind": "premium",
        "affiliate_type": "familiar",
        "scenario": "con_servicio",
        "label": "Con servicio funerario prestado (cónyuge)",
    },
    {
        "key": "empresarial",
        "business_name": "Constructora XYZ S.A.S.",
        "email": "contacto@xyz.com",
        "document_type": "NIT",
        "document_number": "900001001",
        "mobile": "3001001005",
        "address": "Carrera 50 # 80-30",
        "plan_kind": "estandar",
        "affiliate_type": "empresarial",
        "scenario": "recien_firmado",
        "label": "Empresarial · recién firmado, 1 cuota emitida",
    },
]


# ---------------------------------------------------------------- Utilidades


def _addr() -> str:
    return f"{random.choice(STREETS)} {random.randint(1, 60)} # {random.randint(1, 80)}-{random.randint(1, 99):02d}"


def _mobile() -> str:
    return f"3{random.randint(0, 5)}{random.randint(10_000_000, 99_999_999)}"


def _doc() -> str:
    return str(random.randint(10_000_000, 1_500_000_000))


def _random_person(gender: str | None = None) -> tuple[str, str, str]:
    """Returns (first_name, last_name, gender)."""
    g = gender or random.choice(["M", "F"])
    first = random.choice(FIRST_NAMES_M if g == "M" else FIRST_NAMES_F)
    last = f"{random.choice(LAST_NAMES)} {random.choice(LAST_NAMES)}"
    return first, last, g


def _email_for(first: str, last: str, suffix: int) -> str:
    n = (
        first.lower().replace(" ", "").replace("ó", "o").replace("í", "i").replace("á", "a").replace("é", "e").replace("ú", "u")
        + "."
        + last.split()[0].lower().replace("ó", "o").replace("í", "i").replace("á", "a").replace("é", "e").replace("ú", "u").replace("ñ", "n")
        + str(suffix)
        + "@demo.com"
    )
    return n


# ---------------------------------------------------------------- DB helpers


async def _get_or_create_user(db: AsyncSession) -> User:
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
        print(f"  + usuario admin: {DEMO_EMAIL}")
    else:
        user.password_hash = hash_password(DEMO_PASSWORD)
        print(f"  ~ usuario admin existente: {DEMO_EMAIL} (password reseteado)")
    return user


async def _get_or_create_org(db: AsyncSession) -> Organization:
    org = await db.scalar(select(Organization).where(Organization.slug == DEMO_ORG_SLUG))
    if org is None:
        org = Organization(
            id=uuid.uuid4(),
            name=DEMO_ORG_NAME,
            slug=DEMO_ORG_SLUG,
            type="business",
            business_type="funeraria",
            settings={"demo": True},
        )
        db.add(org)
        await db.flush()
        print(f"  + org creada: {DEMO_ORG_NAME} ({DEMO_ORG_SLUG})")
    else:
        print(f"  ~ org existente: {DEMO_ORG_NAME}")
    return org


async def _ensure_membership(db: AsyncSession, user: User, org: Organization) -> None:
    m = await db.scalar(
        select(Membership).where(
            Membership.organization_id == org.id,
            Membership.user_id == user.id,
        )
    )
    if m is None:
        db.add(Membership(
            id=uuid.uuid4(),
            organization_id=org.id,
            user_id=user.id,
            role="owner",
        ))
        await db.flush()
        print("  + membership owner")
    elif m.role != "owner":
        m.role = "owner"
        await db.flush()
        print("  ~ membership promoted a owner")


async def _ensure_memorial_app(db: AsyncSession, org: Organization) -> None:
    reg = await db.scalar(select(AppRegistry).where(AppRegistry.code == "memorial"))
    if reg is None:
        print("  ! WARN: memorial no está en app_registry — la org no la verá activa")
        return
    existing = await db.scalar(
        select(OrganizationApp).where(
            OrganizationApp.organization_id == org.id,
            OrganizationApp.app_id == reg.id,
        )
    )
    if existing is None:
        db.add(OrganizationApp(
            id=uuid.uuid4(),
            organization_id=org.id,
            app_id=reg.id,
            status="active",
            activated_at=datetime.utcnow(),
        ))
        await db.flush()
        print("  + memorial activada en la org")
    else:
        existing.status = "active"
        await db.flush()
        print("  ~ memorial ya activa")


async def _wipe_memorial(db: AsyncSession, org_id: uuid.UUID) -> None:
    """Wipe en orden hijo → padre."""
    for model in (
        MemorialAuditLog,
        MemorialPaymentInvoice,
        MemorialPayment,
        MemorialInvoice,
        MemorialServiceEvent,
        MemorialServiceFamily,
        MemorialTransfer,
        MemorialService,
        MemorialAttendance,
        MemorialInventoryMovement,
        MemorialInventoryItem,
        MemorialEmployee,
        MemorialPosition,
        MemorialDriver,
        MemorialVehicle,
        MemorialRoom,
        MemorialOven,
        MemorialLocation,
        MemorialLeadCommunication,
        MemorialLead,
        MemorialExequialBeneficiary,
        MemorialExequialContract,
        MemorialExequialPlan,
    ):
        if hasattr(model, "organization_id"):
            await db.execute(delete(model).where(model.organization_id == org_id))
        else:
            # Tablas asociativas (payment_invoices) — los borraron las cascades arriba
            pass
    await db.flush()
    print("  - tablas memorial_* limpias para la org demo")


# ---------------------------------------------------------------- Seed steps


async def _seed_plans(db: AsyncSession, org_id: uuid.UUID) -> dict[str, MemorialExequialPlan]:
    """3 planes: económico, estándar, premium — uno por cada plan_type."""
    plans: dict[str, MemorialExequialPlan] = {}

    plans["economico"] = await PlansService.create_plan(db, org_id, PlanCreate(
        code="PLAN-ECO",
        name="Plan Económico Familiar",
        description="Cobertura básica para grupos familiares pequeños.",
        plan_type="familiar",
        max_beneficiaries=4,
        max_age_at_affiliation=70,
        max_age_for_coverage=85,
        waiting_period_days=90,
        monthly_fee=Decimal("30000"),
        quarterly_fee=Decimal("85000"),
        semiannual_fee=Decimal("165000"),
        annual_fee=Decimal("320000"),
        coverage_amount=Decimal("8000000"),
        coverage_items=["Cofre estándar", "Velación 12h", "Carroza", "Cremación o entierro"],
        is_active=True,
        valid_from=date(2025, 1, 1),
    ))
    plans["estandar"] = await PlansService.create_plan(db, org_id, PlanCreate(
        code="PLAN-EST",
        name="Plan Estándar",
        description="Cobertura intermedia individual o empresarial.",
        plan_type="individual",
        max_beneficiaries=1,
        max_age_at_affiliation=75,
        max_age_for_coverage=90,
        waiting_period_days=60,
        monthly_fee=Decimal("55000"),
        quarterly_fee=Decimal("155000"),
        semiannual_fee=Decimal("300000"),
        annual_fee=Decimal("580000"),
        coverage_amount=Decimal("15000000"),
        coverage_items=["Cofre madera", "Velación 24h", "Carroza", "Cremación o entierro", "Tanatopraxia"],
        is_active=True,
        valid_from=date(2025, 1, 1),
    ))
    plans["estandar_empresarial"] = await PlansService.create_plan(db, org_id, PlanCreate(
        code="PLAN-EMP",
        name="Plan Estándar Empresarial",
        description="Cobertura empresarial para empleados y sus familias.",
        plan_type="empresarial",
        max_beneficiaries=20,
        max_age_at_affiliation=70,
        max_age_for_coverage=85,
        waiting_period_days=30,
        monthly_fee=Decimal("450000"),
        quarterly_fee=Decimal("1300000"),
        semiannual_fee=Decimal("2500000"),
        annual_fee=Decimal("4800000"),
        coverage_amount=Decimal("20000000"),
        coverage_items=["Cofre premium", "Velación 24h", "Carroza familiar", "Cremación o entierro", "Tanatopraxia", "Misa"],
        is_active=True,
        valid_from=date(2025, 1, 1),
    ))
    plans["premium"] = await PlansService.create_plan(db, org_id, PlanCreate(
        code="PLAN-PREM",
        name="Plan Premium Familiar",
        description="Cobertura completa para toda la familia con servicios adicionales.",
        plan_type="familiar",
        max_beneficiaries=8,
        max_age_at_affiliation=75,
        max_age_for_coverage=95,
        waiting_period_days=30,
        monthly_fee=Decimal("95000"),
        quarterly_fee=Decimal("270000"),
        semiannual_fee=Decimal("520000"),
        annual_fee=Decimal("1000000"),
        coverage_amount=Decimal("25000000"),
        coverage_items=[
            "Cofre premium", "Velación 24h", "Carroza familiar",
            "Cremación o entierro", "Tanatopraxia", "Misa",
            "Asistencia psicológica", "Traslado nacional",
        ],
        is_active=True,
        valid_from=date(2025, 1, 1),
    ))
    print(f"  + 4 planes creados")
    return plans


async def _seed_positions_and_employees(
    db: AsyncSession, org_id: uuid.UUID,
) -> list[MemorialEmployee]:
    pos_director = MemorialPosition(
        organization_id=org_id, code="DIR", name="Director funerario",
        description="Responsable general de la operación.",
    )
    pos_coord = MemorialPosition(
        organization_id=org_id, code="COORD", name="Coordinador de servicios",
        description="Coordina cada servicio funerario en sitio.",
    )
    pos_aux = MemorialPosition(
        organization_id=org_id, code="AUX", name="Auxiliar funerario",
        description="Apoya velaciones, traslados y preparación.",
    )
    pos_cond = MemorialPosition(
        organization_id=org_id, code="COND", name="Conductor",
        description="Operación de carrozas y vehículos.",
    )
    db.add_all([pos_director, pos_coord, pos_aux, pos_cond])
    await db.flush()

    employees: list[MemorialEmployee] = []
    employee_spec = [
        ("DIR-001", "Roberto", "Salazar Vega", pos_director, Decimal("4500000"), "administrative"),
        ("COORD-001", "Sandra", "Marín Bedoya", pos_coord, Decimal("2800000"), "morning"),
        ("COORD-002", "Felipe", "Quintero Ruiz", pos_coord, Decimal("2800000"), "afternoon"),
        ("AUX-001", "Pedro", "Hernández Castro", pos_aux, Decimal("1700000"), "rotating"),
        ("AUX-002", "Camilo", "Vargas Acosta", pos_aux, Decimal("1700000"), "night"),
        ("AUX-003", "Diana", "Romero Henao", pos_aux, Decimal("1700000"), "morning"),
        ("COND-001", "Hernán", "Torres Pulido", pos_cond, Decimal("1900000"), "rotating"),
        ("COND-002", "Iván", "Cárdenas Marín", pos_cond, Decimal("1900000"), "night"),
    ]
    for code, fn, ln, pos, salary, shift in employee_spec:
        emp = MemorialEmployee(
            organization_id=org_id,
            code=code,
            first_name=fn,
            last_name=ln,
            document_type="CC",
            document_number=_doc(),
            email=_email_for(fn, ln, 0).replace("0@", "@"),
            mobile=_mobile(),
            address=_addr(),
            position_id=pos.id,
            contract_type="indefinido",
            hire_date=date(2024, random.randint(1, 12), random.randint(1, 28)),
            base_salary=salary,
            default_shift=shift,
            status="active",
        )
        db.add(emp)
        employees.append(emp)
    await db.flush()
    print(f"  + 4 cargos + 8 empleados creados")
    return employees


async def _seed_attendance(
    db: AsyncSession, org_id: uuid.UUID, employees: list[MemorialEmployee],
) -> int:
    """Últimos 14 días de asistencia (lun-vie) para todos los empleados."""
    count = 0
    today = TODAY
    for d_offset in range(14, 0, -1):
        d = today - timedelta(days=d_offset)
        if d.weekday() >= 5:
            continue
        for emp in employees:
            # 90% presente, 5% tarde, 5% ausente
            r = random.random()
            if r < 0.90:
                status = "present"
            elif r < 0.95:
                status = "late"
            else:
                status = "absent"
            check_in = datetime.combine(d, datetime.min.time(), tzinfo=UTC).replace(hour=8 if status != "late" else 9)
            check_out = check_in.replace(hour=17)
            db.add(MemorialAttendance(
                organization_id=org_id,
                employee_id=emp.id,
                work_date=d,
                check_in_at=check_in if status != "absent" else None,
                check_out_at=check_out if status != "absent" else None,
                hours_worked=Decimal("9.00") if status == "present" else (Decimal("8.00") if status == "late" else None),
                status=status,
            ))
            count += 1
    await db.flush()
    return count


async def _seed_logistics(
    db: AsyncSession, org_id: uuid.UUID, employees: list[MemorialEmployee],
) -> dict:
    """Vehículos, conductores, salas, hornos, locations."""
    # Vehículos
    veh1 = MemorialVehicle(
        organization_id=org_id, code="V-01", plate="WXY-123",
        type="hearse", brand="Chevrolet", model="N400", year=2022,
        capacity=2, status="active",
    )
    veh2 = MemorialVehicle(
        organization_id=org_id, code="V-02", plate="WZA-456",
        type="family", brand="Renault", model="Master", year=2021,
        capacity=12, status="active",
    )
    db.add_all([veh1, veh2])
    await db.flush()

    # Conductores (vinculados nominalmente a los empleados COND)
    cond_emps = [e for e in employees if e.code.startswith("COND")]
    drv1 = MemorialDriver(
        organization_id=org_id, code="DRV-001",
        first_name=cond_emps[0].first_name, last_name=cond_emps[0].last_name,
        document_type="CC", document_number=cond_emps[0].document_number,
        license_number="B-123456", license_category="C1",
        mobile=cond_emps[0].mobile, is_active=True,
    )
    drv2 = MemorialDriver(
        organization_id=org_id, code="DRV-002",
        first_name=cond_emps[1].first_name, last_name=cond_emps[1].last_name,
        document_type="CC", document_number=cond_emps[1].document_number,
        license_number="B-789012", license_category="C1",
        mobile=cond_emps[1].mobile, is_active=True,
    )
    db.add_all([drv1, drv2])

    # Salas
    sala1 = MemorialRoom(
        organization_id=org_id, code="S-01", name="Sala Principal",
        capacity=80, is_active=True,
    )
    sala2 = MemorialRoom(
        organization_id=org_id, code="S-02", name="Sala Familiar",
        capacity=40, is_active=True,
    )
    db.add_all([sala1, sala2])

    # Horno
    horno = MemorialOven(
        organization_id=org_id, code="H-01", name="Horno Crematorio Principal",
        is_active=True,
    )
    db.add(horno)

    # Locations
    cem = MemorialLocation(
        organization_id=org_id, code="CEM-01", name="Cementerio Central",
        kind="cemetery", address="Carrera 30 # 50-20",
    )
    iglesia = MemorialLocation(
        organization_id=org_id, code="IGL-01", name="Iglesia San Rafael",
        kind="church", address="Calle 15 # 8-25",
    )
    db.add_all([cem, iglesia])

    await db.flush()
    print(f"  + 2 vehículos + 2 conductores + 2 salas + 1 horno + 2 locations")
    return {
        "vehicles": [veh1, veh2], "drivers": [drv1, drv2],
        "rooms": [sala1, sala2], "ovens": [horno],
        "cemetery": cem, "church": iglesia,
    }


async def _seed_inventory(db: AsyncSession, org_id: uuid.UUID) -> list[MemorialInventoryItem]:
    items_spec = [
        ("INV-001", "Cofre madera Roble", "casket", "unidad", 8, 2, Decimal("850000"), Decimal("1500000")),
        ("INV-002", "Cofre madera Premium", "casket", "unidad", 4, 1, Decimal("1500000"), Decimal("2800000")),
        ("INV-003", "Urna cremación estándar", "urn", "unidad", 12, 3, Decimal("180000"), Decimal("350000")),
        ("INV-004", "Urna premium grabada", "urn", "unidad", 6, 1, Decimal("450000"), Decimal("850000")),
        ("INV-005", "Arreglo floral familiar", "flowers", "unidad", 15, 5, Decimal("120000"), Decimal("220000")),
        ("INV-006", "Arreglo floral premium", "flowers", "unidad", 8, 2, Decimal("280000"), Decimal("450000")),
        ("INV-007", "Velas blancas (par)", "supplies", "unidad", 40, 10, Decimal("18000"), Decimal("35000")),
        ("INV-008", "Combustible carroza", "vehicle_supplies", "galón", 30, 8, Decimal("13000"), Decimal("0")),
    ]
    items = []
    for i, (code, name, cat, unit, stock, min_s, cost, price) in enumerate(items_spec, start=1):
        item = MemorialInventoryItem(
            organization_id=org_id, code=code, name=name, category=cat,
            unit=unit, current_stock=Decimal(stock), min_stock=Decimal(min_s),
            unit_cost=cost, sale_price=price, is_active=True,
        )
        db.add(item)
        items.append(item)
    await db.flush()

    # Movimientos: stock inicial documentado
    for i, item in enumerate(items, start=1):
        db.add(MemorialInventoryMovement(
            organization_id=org_id, consecutive=i, code=f"MOV-{i:04d}",
            item_id=item.id, movement_type="entry", quantity=item.current_stock,
            unit_cost=item.unit_cost, reason="Stock inicial",
            movement_date=date(2025, 12, 1),
        ))
    await db.flush()
    print(f"  + 8 items inventario + 8 movimientos de stock inicial")
    return items


# ---------------------------------------------------------------- Contratos


def _add_months(d: date, n: int) -> date:
    """Suma n meses preservando el día (con clamp a fin de mes)."""
    y = d.year + (d.month - 1 + n) // 12
    m = (d.month - 1 + n) % 12 + 1
    # Fin de mes seguro
    try:
        return d.replace(year=y, month=m)
    except ValueError:
        # Día 31 en mes de 30, etc — usar último día válido
        from calendar import monthrange
        last = monthrange(y, m)[1]
        return date(y, m, min(d.day, last))


async def _create_contract_with_history(
    db: AsyncSession,
    org_id: uuid.UUID,
    plan: MemorialExequialPlan,
    titular: dict,
    scenario: str,
    actor_user_id: uuid.UUID,
    invoice_consec_state: dict,  # {"next": int}
    payment_consec_state: dict,  # {"next": int}
    beneficiary_count: int = 0,
) -> MemorialExequialContract:
    """Crea contrato + cuotas históricas (inserción directa) + pagos según escenario."""
    today = TODAY

    # Determinar start_date según escenario
    if scenario == "recien_firmado":
        start = today - timedelta(days=10)
    else:
        start = (today.replace(day=1) - timedelta(days=180)).replace(day=1)

    # Beneficiarios
    benefs: list[BeneficiaryCreate] = []
    if titular.get("business_name"):
        benefs.append(BeneficiaryCreate(
            first_name=titular["business_name"][:40], last_name=None,
            document_type=titular["document_type"],
            document_number=titular["document_number"],
            is_titular=True, joined_at=start,
        ))
    else:
        benefs.append(BeneficiaryCreate(
            first_name=titular["first_name"], last_name=titular["last_name"],
            document_type=titular["document_type"],
            document_number=titular["document_number"],
            is_titular=True, joined_at=start,
        ))
        for _ in range(beneficiary_count):
            fn, ln, _ = _random_person()
            benefs.append(BeneficiaryCreate(
                first_name=fn, last_name=ln,
                document_type=random.choice(DOC_TYPES),
                document_number=_doc(),
                relationship=random.choice(RELATIONSHIPS),
                is_titular=False, joined_at=start,
            ))

    payload = ContractCreate(
        plan_id=plan.id, affiliate_type=plan.plan_type,
        titular_first_name=titular.get("first_name"),
        titular_last_name=titular.get("last_name"),
        titular_business_name=titular.get("business_name"),
        titular_document_type=titular["document_type"],
        titular_document_number=titular["document_number"],
        titular_email=titular["email"], titular_phone=None,
        titular_mobile=titular.get("mobile"), titular_address=titular.get("address"),
        payment_frequency="monthly", start_date=start,
        notes=f"Demo · escenario: {scenario}",
        beneficiaries=benefs,
    )
    contract = await ContractsService.create_contract(db, org_id, payload, actor_user_id)

    # Generar cuotas directamente (sin batch_generate_dues) — más rápido
    fee = Decimal(contract.fee_amount)
    titular_full = (
        titular.get("business_name")
        or f"{titular.get('first_name', '')} {titular.get('last_name', '')}".strip()
    )

    # Periodos: start, start+1m, start+2m, ... mientras period_start <= today
    invoices_for_pay: list[tuple[uuid.UUID, Decimal, date]] = []  # (id, total, due_date)
    period_start = start
    while period_start <= today:
        period_end = _add_months(period_start, 1)
        due_date = period_start + timedelta(days=10)
        consec = invoice_consec_state["next"]
        invoice_consec_state["next"] += 1
        inv = MemorialInvoice(
            organization_id=org_id,
            consecutive=consec,
            code=f"FAC-{consec:04d}",
            source_type="exequial_dues",
            contract_id=contract.id,
            period_start=period_start,
            period_end=period_end,
            issue_date=period_start,
            due_date=due_date,
            subtotal=fee,
            total=fee,
            balance=fee,
            paid_amount=Decimal("0"),
            status="overdue" if due_date < today else "pending",
            description=f"Cuota plan exequial · {period_start.isoformat()}",
            responsible_name=titular_full,
            responsible_document=titular["document_number"],
            responsible_email=titular.get("email"),
            responsible_phone=titular.get("mobile"),
            created_by=actor_user_id,
        )
        db.add(inv)
        await db.flush()
        invoices_for_pay.append((inv.id, fee, due_date))
        period_start = period_end

    # Avanzar contract.next_payment_date al siguiente periodo no facturado
    contract.next_payment_date = period_start

    # Decidir cuántas pagar según escenario
    if scenario in ("al_dia", "con_servicio"):
        to_pay_idx = list(range(len(invoices_for_pay)))
    elif scenario == "mora_leve":
        to_pay_idx = list(range(max(0, len(invoices_for_pay) - 1)))
    elif scenario == "mora_fuerte":
        to_pay_idx = list(range(min(2, len(invoices_for_pay))))
    elif scenario == "recien_firmado":
        to_pay_idx = []
    else:
        to_pay_idx = list(range(len(invoices_for_pay)))

    # Insertar pagos + allocations directamente
    for idx in to_pay_idx:
        inv_id, amt, due = invoices_for_pay[idx]
        pcons = payment_consec_state["next"]
        payment_consec_state["next"] += 1
        payment = MemorialPayment(
            organization_id=org_id,
            consecutive=pcons,
            code=f"REC-{pcons:04d}",
            contract_id=contract.id,
            payer_name=titular_full,
            payer_document=titular["document_number"],
            payer_email=titular.get("email"),
            payer_phone=titular.get("mobile"),
            payment_date=due - timedelta(days=random.randint(0, 5)),
            amount=amt,
            method=random.choice(["cash", "transfer", "card"]),
            recorded_by=actor_user_id,
        )
        db.add(payment)
        await db.flush()
        # Allocation
        db.add(MemorialPaymentInvoice(
            payment_id=payment.id, invoice_id=inv_id, amount=amt,
        ))
        # Actualizar la factura
        inv_obj = await db.get(MemorialInvoice, inv_id)
        if inv_obj is not None:
            inv_obj.paid_amount = amt
            inv_obj.balance = Decimal("0")
            inv_obj.status = "paid"
    await db.flush()

    return contract


def _pick_plan(plans: dict, kind: str) -> MemorialExequialPlan:
    return plans[kind]


def _random_plan(plans: dict, weighted: bool = True) -> tuple[str, MemorialExequialPlan]:
    """Selección aleatoria para los 95 contratos no documentados."""
    # Distribución: 30% económico, 50% estándar (individual o empresarial), 20% premium
    r = random.random()
    if r < 0.30:
        return "economico", plans["economico"]
    elif r < 0.78:
        return "estandar", plans["estandar"]
    elif r < 0.82:
        return "estandar_empresarial", plans["estandar_empresarial"]
    else:
        return "premium", plans["premium"]


def _random_scenario() -> str:
    r = random.random()
    if r < 0.65:
        return "al_dia"
    elif r < 0.80:
        return "mora_leve"
    elif r < 0.90:
        return "mora_fuerte"
    else:
        return "recien_firmado"


async def _seed_contracts(
    db: AsyncSession,
    org_id: uuid.UUID,
    plans: dict,
    actor_user_id: uuid.UUID,
) -> tuple[list[MemorialExequialContract], MemorialExequialContract]:
    """Crea 100 contratos: 5 documentados (casos de muestra) + 95 random."""
    all_contracts: list[MemorialExequialContract] = []
    contract_con_servicio: MemorialExequialContract | None = None
    inv_state = {"next": 1}
    pay_state = {"next": 1}

    # 1. Documentados (los 5 casos)
    for case in SAMPLE_PORTAL_CASES:
        plan = _pick_plan(plans, case["plan_kind"])
        if case["affiliate_type"] == "empresarial":
            plan = plans["estandar_empresarial"]
        c = await _create_contract_with_history(
            db, org_id, plan, case, case["scenario"], actor_user_id,
            inv_state, pay_state,
            beneficiary_count=(3 if case["affiliate_type"] == "familiar" else 0),
        )
        all_contracts.append(c)
        if case["scenario"] == "con_servicio":
            contract_con_servicio = c

    # 2. 95 random
    for i in range(95):
        plan_kind, plan = _random_plan(plans)
        scenario = _random_scenario()

        if plan_kind == "estandar_empresarial":
            biz = f"Empresa {random.choice(['Comercial', 'Industrial', 'Servicios'])} #{i + 1:02d}"
            titular = {
                "business_name": biz,
                "first_name": None, "last_name": None,
                "document_type": "NIT",
                "document_number": str(900_000_000 + i),
                "email": f"empresa{i + 1:02d}@demo.com",
                "mobile": _mobile(),
                "address": _addr(),
            }
            bcount = 0
        else:
            fn, ln, _g = _random_person()
            titular = {
                "first_name": fn, "last_name": ln,
                "business_name": None,
                "document_type": random.choice(DOC_TYPES),
                "document_number": _doc(),
                "email": _email_for(fn, ln, i + 100),
                "mobile": _mobile(),
                "address": _addr(),
            }
            if plan.plan_type == "familiar":
                max_extras = max(1, (plan.max_beneficiaries or 4) - 1)
                bcount = random.randint(1, min(3, max_extras))
            else:
                bcount = 0

        c = await _create_contract_with_history(
            db, org_id, plan, titular, scenario, actor_user_id,
            inv_state, pay_state, bcount,
        )
        all_contracts.append(c)
        if (i + 1) % 20 == 0:
            print(f"    ... {len(all_contracts)} / 100 contratos", flush=True)

    print(f"  + {len(all_contracts)} contratos creados (5 documentados + 95 random)")
    assert contract_con_servicio is not None, "Faltó el contrato 'con_servicio'"
    return all_contracts, contract_con_servicio


# ---------------------------------------------------------------- Servicios funerarios


async def _seed_funeral_services(
    db: AsyncSession,
    org_id: uuid.UUID,
    contract_con_servicio: MemorialExequialContract,
    logistics: dict,
    actor_user_id: uuid.UUID,
) -> int:
    """5 servicios funerarios: 1 vinculado al contrato 'con_servicio', 4 sueltos."""
    services = []
    today = TODAY

    # Servicio 1 — vinculado al contrato (cónyuge del Sr. Castaño)
    s1 = MemorialService(
        organization_id=org_id,
        consecutive=1, code="SVC-0001",
        deceased_first_name="Patricia",
        deceased_last_name="Henao Restrepo",
        deceased_document_type="CC", deceased_document_number=_doc(),
        deceased_birth_date=date(1955, 5, 12),
        deceased_death_date=today - timedelta(days=45),
        deceased_death_cause="Causa natural",
        service_type="velacion_entierro",
        status="finalizado",
        velation_start_at=datetime.combine(today - timedelta(days=44), datetime.min.time(), tzinfo=UTC).replace(hour=15),
        velation_end_at=datetime.combine(today - timedelta(days=43), datetime.min.time(), tzinfo=UTC).replace(hour=10),
        burial_at=datetime.combine(today - timedelta(days=43), datetime.min.time(), tzinfo=UTC).replace(hour=11),
        velation_room_id=logistics["rooms"][0].id,
        cemetery_id=logistics["cemetery"].id,
        exequial_contract_id=contract_con_servicio.id,
        estimated_total=Decimal("0"),
        final_total=Decimal("0"),
        closed_at=datetime.combine(today - timedelta(days=43), datetime.min.time(), tzinfo=UTC).replace(hour=18),
        closed_by=actor_user_id,
        created_by=actor_user_id,
        notes="Cobertura por plan exequial Premium.",
    )
    db.add(s1)
    services.append(s1)

    # Otros 4 servicios sueltos
    extra = [
        ("velacion_cremacion", "finalizado", 30, "Carlos", "Martínez López"),
        ("velacion", "en_proceso", 1, "Rosa", "García Vargas"),
        ("velacion_entierro", "finalizado", 80, "Antonio", "Torres Pérez"),
        ("velacion_cremacion_entierro", "finalizado", 120, "Beatriz", "Ramírez Henao"),
    ]
    for i, (stype, status, days_ago, fn, ln) in enumerate(extra, start=2):
        death = today - timedelta(days=days_ago)
        s = MemorialService(
            organization_id=org_id,
            consecutive=i, code=f"SVC-{i:04d}",
            deceased_first_name=fn, deceased_last_name=ln,
            deceased_document_type="CC", deceased_document_number=_doc(),
            deceased_birth_date=date(random.randint(1935, 1965), random.randint(1, 12), random.randint(1, 28)),
            deceased_death_date=death,
            deceased_death_cause="Causa natural",
            service_type=stype, status=status,
            velation_start_at=datetime.combine(death + timedelta(days=1), datetime.min.time(), tzinfo=UTC).replace(hour=15),
            velation_room_id=random.choice(logistics["rooms"]).id,
            cemetery_id=logistics["cemetery"].id if "entierro" in stype else None,
            cremation_oven_id=logistics["ovens"][0].id if "cremacion" in stype else None,
            estimated_total=Decimal(random.randint(3_000_000, 12_000_000)),
            final_total=Decimal(random.randint(3_000_000, 12_000_000)) if status == "finalizado" else Decimal("0"),
            closed_at=datetime.combine(death + timedelta(days=2), datetime.min.time(), tzinfo=UTC) if status == "finalizado" else None,
            closed_by=actor_user_id if status == "finalizado" else None,
            created_by=actor_user_id,
        )
        db.add(s)
        services.append(s)

    await db.flush()

    # Eventos básicos (notas de creación) para cada servicio
    for s in services:
        db.add(MemorialServiceEvent(
            organization_id=org_id, service_id=s.id, actor_user_id=actor_user_id,
            event_type="created", body=f"Servicio creado para {s.deceased_first_name} {s.deceased_last_name}.",
        ))
    await db.flush()
    print(f"  + {len(services)} servicios funerarios creados")
    return len(services)


# ---------------------------------------------------------------- CRM Leads


async def _seed_crm_leads(
    db: AsyncSession, org_id: uuid.UUID, actor_user_id: uuid.UUID,
) -> int:
    leads_spec = [
        ("Mariana", "Bedoya López", "mariana.bedoya@example.com", "whatsapp", "exequial_plan", "new", "high"),
        ("Roberto", "Cano Mendoza", "roberto.cano@example.com", "phone", "exequial_plan", "contacted", "medium"),
        ("Empresarial Norte SAS", None, "ventas@norte.com", "web", "exequial_plan", "qualified", "high"),
        ("Lucía", "Restrepo Vargas", "lucia.restrepo@example.com", "referral", "service_future", "proposal", "medium"),
        ("Manuel", "Ávila Castro", "manuel.avila@example.com", "walk_in", "info", "lost", "low"),
        ("Sofía", "Marín Hernández", "sofia.marin@example.com", "social", "exequial_plan", "new", "medium"),
        ("Pedro", "Quintero Salazar", "pedro.quintero@example.com", "whatsapp", "exequial_plan", "contacted", "high"),
        ("Andrea", "Ospina Pulido", "andrea.ospina@example.com", "phone", "service_immediate", "proposal", "urgent"),
        ("Daniel", "Castaño Marín", "daniel.castano@example.com", "referral", "exequial_plan", "won", "high"),
        ("Inversiones Sur", None, "contacto@sur.com", "web", "exequial_plan", "qualified", "medium"),
    ]
    created = []
    for fn, ln, email, source, interest, status, priority in leads_spec:
        is_business = ln is None
        lead_data = LeadCreate(
            first_name=None if is_business else fn,
            last_name=ln,
            business_name=fn if is_business else None,
            email=email,
            mobile=_mobile(),
            address=_addr(),
            source=source,
            interest=interest,
            priority=priority,
            notes=f"Lead demo · interés {interest}",
        )
        lead = await LeadsService.create(db, org_id, lead_data, actor_user_id)
        # Forzar el status (LeadsService.create siempre crea con status='new')
        if status != "new":
            lead.status = status
            if status == "won":
                lead.converted_at = datetime.now(UTC)
            await db.flush()
        created.append(lead)

        # Una comunicación por lead
        db.add(MemorialLeadCommunication(
            organization_id=org_id, lead_id=lead.id,
            channel=("call" if source == "phone" else "whatsapp" if source == "whatsapp" else "note"),
            direction="outbound",
            subject="Primer contacto",
            content=f"Llamada inicial sobre {interest}.",
            occurred_at=datetime.now(UTC) - timedelta(days=random.randint(1, 20)),
            created_by=actor_user_id,
        ))
    await db.flush()
    print(f"  + {len(created)} leads CRM + comunicaciones")
    return len(created)


# ---------------------------------------------------------------- Summary


def _print_credentials_summary() -> None:
    print()
    print("=" * 72)
    print("CREDENCIALES DEMO · Funeraria San Rafael")
    print("=" * 72)
    print()
    print("ADMINISTRADOR (entra a SavvyCore como dueño de la funeraria):")
    print(f"  URL:      https://app.savvypos.com/signin")
    print(f"  Email:    {DEMO_EMAIL}")
    print(f"  Password: {DEMO_PASSWORD}")
    print()
    print("PORTAL DEL CLIENTE (5 cuentas de muestra · sin contraseña):")
    print(f"  URL:      https://app.savvypos.com/memorial-portal")
    print(f"  Slug org: {DEMO_ORG_SLUG}")
    print()
    for i, case in enumerate(SAMPLE_PORTAL_CASES, start=1):
        name = case.get("business_name") or f"{case.get('first_name')} {case.get('last_name')}"
        print(f"  {i}. {case['label']}")
        print(f"     Titular:    {name}")
        print(f"     Email:      {case['email']}")
        print(f"     Documento:  {case['document_type']} {case['document_number']}")
        print()
    print("Los otros 95 contratos también son accesibles vía portal con email/doc")
    print("del titular registrado (todos terminan en @demo.com / docs 10M–1.5B).")
    print("=" * 72)


# ---------------------------------------------------------------- Main


async def main() -> None:
    print("=" * 72)
    print("SavvyMemorial · seed demo (100 contratos, Funeraria San Rafael)")
    print("=" * 72)
    async with async_session_factory() as db:
        print("\n[1/9] Usuario admin y org…")
        user = await _get_or_create_user(db)
        org = await _get_or_create_org(db)
        await _ensure_membership(db, user, org)
        await _ensure_memorial_app(db, org)

        print("\n[2/9] Wipe memorial_* para la org demo…")
        await _wipe_memorial(db, org.id)

        print("\n[3/9] Planes exequiales…")
        plans = await _seed_plans(db, org.id)

        print("\n[4/9] Cargos + empleados…")
        employees = await _seed_positions_and_employees(db, org.id)

        print("\n[5/9] Asistencia (14 días lun-vie)…")
        att = await _seed_attendance(db, org.id, employees)
        print(f"  + {att} registros de asistencia")

        print("\n[6/9] Logística (vehículos, salas, hornos, locations)…")
        logistics = await _seed_logistics(db, org.id, employees)

        print("\n[7/9] Inventario…")
        await _seed_inventory(db, org.id)

        print("\n[8/9] 100 contratos con cuotas + pagos…")
        all_contracts, contract_servicio = await _seed_contracts(db, org.id, plans, user.id)

        print("\n[9/9] Servicios funerarios + leads CRM…")
        await _seed_funeral_services(db, org.id, contract_servicio, logistics, user.id)
        await _seed_crm_leads(db, org.id, user.id)

        await db.commit()
        print("\nOK — commit aplicado.")

        # Stats finales
        from sqlalchemy import func as _func
        n_inv = await db.scalar(select(_func.count(MemorialInvoice.id)).where(MemorialInvoice.organization_id == org.id)) or 0
        n_pay = await db.scalar(select(_func.count(MemorialPayment.id)).where(MemorialPayment.organization_id == org.id)) or 0
        cart = await db.scalar(
            select(_func.coalesce(_func.sum(MemorialInvoice.balance), 0))
            .where(
                MemorialInvoice.organization_id == org.id,
                MemorialInvoice.status.in_(["pending", "partial", "overdue"]),
            )
        ) or Decimal("0")
        print(f"\nStats: {len(all_contracts)} contratos · {n_inv} cuotas · {n_pay} pagos · cartera $ {int(cart):,}".replace(",", "."))

    await engine.dispose()
    _print_credentials_summary()


if __name__ == "__main__":
    asyncio.run(main())
