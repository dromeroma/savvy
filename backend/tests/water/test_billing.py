"""Tests for SavvyWater billing engine — basic/excess pricing."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.invoices.schemas import GenerateInvoiceRequest
from src.apps.water.invoices.service import InvoicesService
from src.apps.water.models import WaterMeter, WaterSubscriber, WaterTariff
from src.core.exceptions import ConflictError, ValidationError


@pytest.mark.asyncio
async def test_consumption_within_basic_limit_charges_basic_only(
    db: AsyncSession, org, subscriber: WaterSubscriber, meter: WaterMeter,
    tariff_basic: WaterTariff, make_consumption,
):
    """15 m³ con límite básico de 20 → solo cargo básico + cargo fijo."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)

    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )

    # fixed 5,000 + 15 m³ * 2,000 = 35,000
    assert inv.consumption_cubic == Decimal("15")
    assert inv.fixed_charge == Decimal("5000")
    assert inv.consumption_charge == Decimal("30000")
    assert inv.total == Decimal("35000")
    assert inv.balance == Decimal("35000")
    assert inv.status == "pending"


@pytest.mark.asyncio
async def test_consumption_exactly_at_basic_limit_no_surplus(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """20 m³ = límite básico → todo en básico, $0 excedente."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 20)

    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )

    # 5,000 + 20 * 2,000 = 45,000
    assert inv.consumption_charge == Decimal("40000")
    assert inv.total == Decimal("45000")


@pytest.mark.asyncio
async def test_consumption_above_basic_charges_surplus(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """35 m³ → 20 básicos a $2,000 + 15 excedente a $3,500."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 35)

    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )

    # fixed 5,000 + (20*2000) + (15*3500) = 5,000 + 40,000 + 52,500 = 97,500
    assert inv.consumption_charge == Decimal("92500")
    assert inv.total == Decimal("97500")


@pytest.mark.asyncio
async def test_no_tariff_raises_validation_error(
    db: AsyncSession, org, subscriber, meter, make_consumption,
):
    """Si no hay tarifa configurada, debe rechazar."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 10)

    with pytest.raises(ValidationError):
        await InvoicesService.generate_from_consumption(
            db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
        )


@pytest.mark.asyncio
async def test_expired_tariff_not_selected(
    db: AsyncSession, org, subscriber, meter, make_consumption,
):
    """Tarifa con valid_to en el pasado no debe aplicar."""
    from src.apps.water.models import WaterTariff
    import uuid as _uuid
    expired = WaterTariff(
        id=_uuid.uuid4(),
        organization_id=org.id,
        code="OLD",
        name="Tarifa expirada",
        subscriber_type="residential",
        stratum=3,
        fixed_charge=Decimal("1000"),
        price_per_cubic=Decimal("100"),
        is_active=True,
        valid_from=date(2020, 1, 1),
        valid_to=date(2024, 12, 31),
    )
    db.add(expired)
    await db.flush()

    cons = await make_consumption(meter, subscriber, 2026, 1, 10)

    # generate_from_consumption uses issue_date=today which is 2026 — out of range
    with pytest.raises(ValidationError):
        await InvoicesService.generate_from_consumption(
            db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
        )


@pytest.mark.asyncio
async def test_cannot_invoice_same_consumption_twice(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)

    await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )
    with pytest.raises(ConflictError):
        await InvoicesService.generate_from_consumption(
            db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
        )


@pytest.mark.asyncio
async def test_consecutive_increments_per_org(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Cada factura nueva debe tener consecutivo = max + 1."""
    c1 = await make_consumption(meter, subscriber, 2026, 1, 10)
    c2 = await make_consumption(meter, subscriber, 2026, 2, 10)

    inv1 = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=c1.id),
    )
    inv2 = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=c2.id),
    )
    assert inv1.consecutive == 1
    assert inv2.consecutive == 2


@pytest.mark.asyncio
async def test_discount_does_not_make_total_negative(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Descuento mayor al total → total = 0, no negativo."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 5)

    inv = await InvoicesService.generate_from_consumption(
        db, org.id,
        GenerateInvoiceRequest(
            consumption_id=cons.id, discounts=Decimal("999999"),
        ),
    )
    assert inv.total == Decimal("0")
