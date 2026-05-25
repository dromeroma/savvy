"""Tests for SavvyWater cartera service — mora idempotente."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.cartera.service import CarteraService
from src.apps.water.invoices.schemas import GenerateInvoiceRequest
from src.apps.water.invoices.service import InvoicesService


@pytest.mark.asyncio
async def test_overdue_invoice_gets_interest_applied(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Factura vencida 30 días con tarifa 2.5% mensual → interés aplicado."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    # Issue date 60 días en el pasado, due_date 45 días en el pasado
    today = date(2026, 3, 15)
    past_issue = today - timedelta(days=60)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id,
        GenerateInvoiceRequest(
            consumption_id=cons.id,
            issue_date=past_issue,
            due_date=past_issue + timedelta(days=15),  # vencida hace 45 días
        ),
    )
    base_total = Decimal(inv.total)

    result = await CarteraService.recalc_overdue(db, org.id, on_date=today)

    await db.refresh(inv)
    # 45 días vencida → ceil(45/30) = 2 meses
    # interés = base * 0.025 * 2 = base * 0.05
    expected_interest = (base_total * Decimal("0.05")).quantize(Decimal("0.01"))
    assert inv.late_interest == expected_interest
    assert inv.status == "overdue"
    assert inv.total == base_total + expected_interest
    assert inv.balance == base_total + expected_interest
    assert result.invoices_marked_overdue == 1
    assert result.invoices_with_interest_applied == 1
    assert result.total_interest_applied == expected_interest


@pytest.mark.asyncio
async def test_recalc_is_idempotent_within_same_month(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Correr recalc dos veces no debe duplicar el interés."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    today = date(2026, 3, 15)
    past_issue = today - timedelta(days=60)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id,
        GenerateInvoiceRequest(
            consumption_id=cons.id,
            issue_date=past_issue,
            due_date=past_issue + timedelta(days=15),
        ),
    )

    await CarteraService.recalc_overdue(db, org.id, on_date=today)
    await db.refresh(inv)
    interest_first = inv.late_interest
    total_first = inv.total

    # Re-run same day — must NOT add more interest
    second = await CarteraService.recalc_overdue(db, org.id, on_date=today)
    await db.refresh(inv)
    assert inv.late_interest == interest_first
    assert inv.total == total_first
    # The second pass adds no new interest
    assert second.invoices_with_interest_applied == 0
    assert second.total_interest_applied == Decimal("0")


@pytest.mark.asyncio
async def test_paid_invoice_does_not_accrue_interest(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Factura ya pagada no debe entrar al recálculo."""
    from src.apps.water.payments.schemas import PaymentCreate
    from src.apps.water.payments.service import PaymentsService

    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    today = date(2026, 3, 15)
    past_issue = today - timedelta(days=60)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id,
        GenerateInvoiceRequest(
            consumption_id=cons.id,
            issue_date=past_issue,
            due_date=past_issue + timedelta(days=15),
        ),
    )
    # Pago completo
    await PaymentsService.register_payment(
        db, org.id,
        PaymentCreate(
            subscriber_id=subscriber.id,
            amount=Decimal(inv.total),
            payment_date=today - timedelta(days=10),
        ),
        collector_user_id=None,
    )
    await db.refresh(inv)
    assert inv.status == "paid"

    result = await CarteraService.recalc_overdue(db, org.id, on_date=today)
    await db.refresh(inv)
    assert inv.late_interest == Decimal("0")
    assert result.invoices_with_interest_applied == 0


@pytest.mark.asyncio
async def test_annulled_invoice_does_not_accrue_interest(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    today = date(2026, 3, 15)
    past_issue = today - timedelta(days=60)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id,
        GenerateInvoiceRequest(
            consumption_id=cons.id,
            issue_date=past_issue,
            due_date=past_issue + timedelta(days=15),
        ),
    )
    await InvoicesService.annul_invoice(db, org.id, inv.id)
    await db.refresh(inv)

    await CarteraService.recalc_overdue(db, org.id, on_date=today)
    await db.refresh(inv)
    assert inv.late_interest == Decimal("0")
    assert inv.status == "annulled"


@pytest.mark.asyncio
async def test_subscriber_marked_overdue_when_invoice_overdue(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Suscriptor active con factura vencida → pasa a overdue."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    today = date(2026, 3, 15)
    past_issue = today - timedelta(days=60)
    await InvoicesService.generate_from_consumption(
        db, org.id,
        GenerateInvoiceRequest(
            consumption_id=cons.id,
            issue_date=past_issue,
            due_date=past_issue + timedelta(days=15),
        ),
    )
    assert subscriber.status == "active"

    result = await CarteraService.recalc_overdue(db, org.id, on_date=today)
    await db.refresh(subscriber)
    assert subscriber.status == "overdue"
    assert result.subscribers_marked_overdue == 1


@pytest.mark.asyncio
async def test_invoice_not_yet_due_no_interest(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Factura cuya due_date es futura → no entra al recálculo."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    today = date(2026, 1, 28)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id,
        GenerateInvoiceRequest(
            consumption_id=cons.id,
            issue_date=today,
            due_date=today + timedelta(days=15),
        ),
    )

    result = await CarteraService.recalc_overdue(db, org.id, on_date=today)
    await db.refresh(inv)
    assert inv.late_interest == Decimal("0")
    assert inv.status == "pending"
    assert result.invoices_marked_overdue == 0


@pytest.mark.asyncio
async def test_zero_rate_tariff_no_interest_even_when_overdue(
    db: AsyncSession, org, subscriber, meter, make_consumption,
):
    """Tarifa con late_interest_rate=0 → factura vencida no acumula."""
    from src.apps.water.models import WaterTariff
    import uuid as _uuid
    no_interest = WaterTariff(
        id=_uuid.uuid4(),
        organization_id=org.id,
        code="NO-INT",
        name="Sin intereses",
        subscriber_type="residential",
        stratum=3,
        fixed_charge=Decimal("1000"),
        price_per_cubic=Decimal("100"),
        late_interest_rate=Decimal("0"),
        is_active=True,
        valid_from=date(2024, 1, 1),
    )
    db.add(no_interest)
    await db.flush()

    cons = await make_consumption(meter, subscriber, 2026, 1, 10)
    today = date(2026, 3, 15)
    past_issue = today - timedelta(days=60)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id,
        GenerateInvoiceRequest(
            consumption_id=cons.id,
            issue_date=past_issue,
            due_date=past_issue + timedelta(days=15),
        ),
    )

    await CarteraService.recalc_overdue(db, org.id, on_date=today)
    await db.refresh(inv)
    assert inv.late_interest == Decimal("0")
    assert inv.status == "overdue"  # marcada vencida, pero sin interés
