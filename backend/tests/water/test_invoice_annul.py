"""Tests for SavvyWater invoice annulment."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.invoices.schemas import GenerateInvoiceRequest
from src.apps.water.invoices.service import InvoicesService
from src.apps.water.payments.schemas import PaymentCreate
from src.apps.water.payments.service import PaymentsService
from src.core.exceptions import ConflictError


@pytest.mark.asyncio
async def test_pending_invoice_can_be_annulled(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )

    result = await InvoicesService.annul_invoice(db, org.id, inv.id)
    assert result.status == "annulled"
    assert result.balance == Decimal("0")


@pytest.mark.asyncio
async def test_already_annulled_invoice_raises_conflict(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )
    await InvoicesService.annul_invoice(db, org.id, inv.id)

    with pytest.raises(ConflictError):
        await InvoicesService.annul_invoice(db, org.id, inv.id)


@pytest.mark.asyncio
async def test_invoice_with_payment_cannot_be_annulled(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Factura con pago aplicado → bloqueada hasta que se anulen los pagos."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )
    await PaymentsService.register_payment(
        db, org.id,
        PaymentCreate(
            subscriber_id=subscriber.id,
            amount=Decimal("10000"),
            payment_date=date(2026, 2, 1),
        ),
        collector_user_id=None,
    )
    await db.refresh(inv)
    assert inv.paid_amount == Decimal("10000")

    with pytest.raises(ConflictError):
        await InvoicesService.annul_invoice(db, org.id, inv.id)


@pytest.mark.asyncio
async def test_can_invoice_same_period_after_annulment(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Tras anular, la lectura debe poder facturarse otra vez."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )
    first_consec = inv.consecutive

    await InvoicesService.annul_invoice(db, org.id, inv.id)

    # Re-facturar — debe generar nuevo consecutivo, no chocar con la anulada
    new_inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )
    assert new_inv.consecutive == first_consec + 1
    assert new_inv.status == "pending"


@pytest.mark.asyncio
async def test_annulled_invoice_does_not_count_in_subscriber_balance(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Una factura anulada no debe contar como deuda — su balance es 0."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )
    original_total = Decimal(inv.total)
    assert original_total > 0

    await InvoicesService.annul_invoice(db, org.id, inv.id)
    await db.refresh(inv)
    assert inv.balance == Decimal("0")
    # total se mantiene (auditoría), pero balance y status reflejan anulación
    assert inv.total == original_total
    assert inv.status == "annulled"
