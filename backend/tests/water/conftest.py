"""Test fixtures for SavvyWater services.

Uses SQLite in-memory per test for isolation + speed. JSONB columns are
compiled as plain JSON so the schema creates cleanly under SQLite.
"""

from __future__ import annotations

import uuid
from collections.abc import AsyncGenerator
from datetime import date
from decimal import Decimal

import pytest_asyncio
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.ext.compiler import compiles


# JSONB → JSON for SQLite. Must be defined before any model import.
@compiles(JSONB, "sqlite")
def _compile_jsonb_sqlite(element, compiler, **kw):  # type: ignore[no-untyped-def]
    return "JSON"


# Importing main registers every model on Base.metadata
from src.apps.water.models import (  # noqa: E402
    WaterConsumption,
    WaterInvoice,
    WaterMeter,
    WaterSubscriber,
    WaterTariff,
)
from src.core.database import Base  # noqa: E402
from src.main import app  # noqa: E402, F401
from src.modules.auth.models import User  # noqa: E402
from src.modules.organization.models import Organization  # noqa: E402


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database():
    """Override the root conftest's Postgres setup — water tests use
    SQLite in-memory and don't need the global setup."""
    yield


@pytest_asyncio.fixture
async def db() -> AsyncGenerator[AsyncSession, None]:
    """Brand-new SQLite DB per test. Schema is created + dropped each call.

    No commits — we operate inside a single open session and flush as needed.
    """
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    factory = async_sessionmaker(
        bind=engine, class_=AsyncSession, expire_on_commit=False,
    )
    async with factory() as session:
        yield session
        await session.rollback()
    await engine.dispose()


@pytest_asyncio.fixture
async def org(db: AsyncSession) -> Organization:
    o = Organization(
        id=uuid.uuid4(),
        name="Acueducto Test",
        slug=f"test-{uuid.uuid4().hex[:8]}",
        type="business",
        settings={},
    )
    db.add(o)
    await db.flush()
    return o


@pytest_asyncio.fixture
async def subscriber(db: AsyncSession, org: Organization) -> WaterSubscriber:
    s = WaterSubscriber(
        id=uuid.uuid4(),
        organization_id=org.id,
        code="SUB-001",
        first_name="Juan",
        last_name="Pérez",
        subscriber_type="residential",
        stratum=3,
        status="active",
    )
    db.add(s)
    await db.flush()
    return s


@pytest_asyncio.fixture
async def meter(
    db: AsyncSession, org: Organization, subscriber: WaterSubscriber,
) -> WaterMeter:
    m = WaterMeter(
        id=uuid.uuid4(),
        organization_id=org.id,
        subscriber_id=subscriber.id,
        serial_number="M-0001",
        initial_reading=Decimal("0"),
        last_reading=Decimal("0"),
        status="active",
    )
    db.add(m)
    await db.flush()
    return m


@pytest_asyncio.fixture
async def tariff_basic(db: AsyncSession, org: Organization) -> WaterTariff:
    """Residential stratum 3 tariff.

    - Fixed charge: $5,000
    - First 20 m³ at $2,000/m³ (basic)
    - Excess at $3,500/m³ (excedente)
    - Late interest: 2.5% mensual
    - Suspension/reconnection fee: $30,000 each
    """
    t = WaterTariff(
        id=uuid.uuid4(),
        organization_id=org.id,
        code="RES-E3",
        name="Residencial Estrato 3",
        subscriber_type="residential",
        stratum=3,
        fixed_charge=Decimal("5000"),
        price_per_cubic=Decimal("2000"),
        basic_limit_cubic=Decimal("20"),
        surplus_price_per_cubic=Decimal("3500"),
        reconnection_fee=Decimal("30000"),
        suspension_fee=Decimal("30000"),
        late_interest_rate=Decimal("0.025"),
        is_active=True,
        valid_from=date(2024, 1, 1),
        valid_to=None,
    )
    db.add(t)
    await db.flush()
    return t


@pytest_asyncio.fixture
async def make_consumption(db: AsyncSession, org: Organization):
    """Factory: create a consumption reading for a given meter+period."""

    async def _make(
        meter: WaterMeter,
        subscriber: WaterSubscriber,
        year: int,
        month: int,
        cubic: int | Decimal,
        previous: Decimal | None = None,
    ) -> WaterConsumption:
        prev = previous if previous is not None else Decimal(meter.last_reading)
        cur = prev + Decimal(cubic)
        c = WaterConsumption(
            id=uuid.uuid4(),
            organization_id=org.id,
            meter_id=meter.id,
            subscriber_id=subscriber.id,
            period_year=year,
            period_month=month,
            reading_date=date(year, month, 28),
            previous_reading=prev,
            current_reading=cur,
            consumption_cubic=Decimal(cubic),
            is_estimated=False,
        )
        db.add(c)
        meter.last_reading = cur
        meter.last_reading_date = c.reading_date
        await db.flush()
        return c

    return _make
