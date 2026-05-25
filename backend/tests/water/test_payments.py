"""Tests for SavvyWater payments — FIFO allocation."""

from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.invoices.schemas import GenerateInvoiceRequest
from src.apps.water.invoices.service import InvoicesService
from src.apps.water.models import WaterInvoice, WaterPaymentInvoice
from src.apps.water.payments.schemas import PaymentCreate
from src.apps.water.payments.service import PaymentsService
from src.core.exceptions import ValidationError


@pytest.mark.asyncio
async def test_full_payment_closes_invoice(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )
    total = Decimal(inv.total)

    await PaymentsService.register_payment(
        db, org.id,
        PaymentCreate(
            subscriber_id=subscriber.id,
            amount=total,
            payment_date=date(2026, 2, 1),
        ),
        collector_user_id=None,
    )
    await db.refresh(inv)
    assert inv.paid_amount == total
    assert inv.balance == Decimal("0")
    assert inv.status == "paid"


@pytest.mark.asyncio
async def test_partial_payment_leaves_balance(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )
    total = Decimal(inv.total)  # 35,000
    half = total / 2

    await PaymentsService.register_payment(
        db, org.id,
        PaymentCreate(
            subscriber_id=subscriber.id,
            amount=half,
            payment_date=date(2026, 2, 1),
        ),
        collector_user_id=None,
    )
    await db.refresh(inv)
    assert inv.paid_amount == half
    assert inv.balance == half
    assert inv.status == "partial"


@pytest.mark.asyncio
async def test_fifo_allocates_to_oldest_first(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """3 facturas, pago cubre las 2 más viejas + parcial en la 3a."""
    base_date = date(2026, 1, 1)
    invoices = []
    for i, month in enumerate((1, 2, 3), start=0):
        cons = await make_consumption(meter, subscriber, 2026, month, 15)
        inv = await InvoicesService.generate_from_consumption(
            db, org.id,
            GenerateInvoiceRequest(
                consumption_id=cons.id,
                issue_date=base_date + timedelta(days=30 * i),
                due_date=base_date + timedelta(days=30 * i + 15),
            ),
        )
        invoices.append(inv)
    # Cada una es 35,000 → total 105,000
    total = Decimal("35000") * 3
    # Pago de 80,000 = paga 1ª + 2ª + 10,000 de la 3ª
    pay_amount = Decimal("80000")

    await PaymentsService.register_payment(
        db, org.id,
        PaymentCreate(
            subscriber_id=subscriber.id,
            amount=pay_amount,
            payment_date=date(2026, 4, 1),
        ),
        collector_user_id=None,
    )
    for inv in invoices:
        await db.refresh(inv)

    assert invoices[0].status == "paid"
    assert invoices[0].balance == Decimal("0")
    assert invoices[1].status == "paid"
    assert invoices[1].balance == Decimal("0")
    assert invoices[2].status == "partial"
    assert invoices[2].balance == Decimal("25000")
    assert invoices[2].paid_amount == Decimal("10000")


@pytest.mark.asyncio
async def test_overpayment_does_not_explode_leaves_credit(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Pago > total de saldo → factura queda en paid, el sobrante
    queda registrado en water_payments.amount sin asignar."""
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )
    total = Decimal(inv.total)
    overpay = total + Decimal("20000")

    payment = await PaymentsService.register_payment(
        db, org.id,
        PaymentCreate(
            subscriber_id=subscriber.id,
            amount=overpay,
            payment_date=date(2026, 2, 1),
        ),
        collector_user_id=None,
    )
    await db.refresh(inv)
    assert inv.status == "paid"
    assert inv.paid_amount == total

    # El pago se registra completo, pero solo se asignó el total a la factura
    assert Decimal(payment.amount) == overpay
    alloc_sum = await db.scalar(
        select(WaterPaymentInvoice).where(WaterPaymentInvoice.payment_id == payment.id)
    )
    # Verify only one allocation row, covering exactly inv.total
    rows = (await db.execute(
        select(WaterPaymentInvoice.amount).where(WaterPaymentInvoice.payment_id == payment.id)
    )).all()
    assert len(rows) == 1
    assert rows[0][0] == total


@pytest.mark.asyncio
async def test_zero_amount_payment_rejected(
    db: AsyncSession, org, subscriber,
):
    """Pago de $0 lo rechaza Pydantic en el schema (gt=0)."""
    from pydantic import ValidationError as PydanticValidationError
    with pytest.raises(PydanticValidationError):
        PaymentCreate(
            subscriber_id=subscriber.id,
            amount=Decimal("0"),
            payment_date=date(2026, 2, 1),
        )


@pytest.mark.asyncio
async def test_explicit_allocation_mismatch_rejected(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Si la suma de allocations != amount, debe rechazar."""
    from src.apps.water.payments.schemas import PaymentAllocationInput
    cons = await make_consumption(meter, subscriber, 2026, 1, 15)
    inv = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons.id),
    )

    with pytest.raises(ValidationError):
        await PaymentsService.register_payment(
            db, org.id,
            PaymentCreate(
                subscriber_id=subscriber.id,
                amount=Decimal("10000"),
                payment_date=date(2026, 2, 1),
                allocations=[
                    PaymentAllocationInput(
                        invoice_id=inv.id, amount=Decimal("5000"),
                    ),
                ],
            ),
            collector_user_id=None,
        )


@pytest.mark.asyncio
async def test_payment_clears_subscriber_overdue_status(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Suscriptor overdue + pago que cubre todo → vuelve a active."""
    from src.apps.water.cartera.service import CarteraService

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
    await db.refresh(subscriber)
    assert subscriber.status == "overdue"

    await db.refresh(inv)
    await PaymentsService.register_payment(
        db, org.id,
        PaymentCreate(
            subscriber_id=subscriber.id,
            amount=Decimal(inv.balance),
            payment_date=today,
        ),
        collector_user_id=None,
    )
    await db.refresh(subscriber)
    assert subscriber.status == "active"


@pytest.mark.asyncio
async def test_payment_to_annulled_invoice_is_skipped(
    db: AsyncSession, org, subscriber, meter, tariff_basic, make_consumption,
):
    """Auto-allocation no debe tocar facturas anuladas."""
    cons1 = await make_consumption(meter, subscriber, 2026, 1, 15)
    inv1 = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons1.id),
    )
    cons2 = await make_consumption(meter, subscriber, 2026, 2, 15)
    inv2 = await InvoicesService.generate_from_consumption(
        db, org.id, GenerateInvoiceRequest(consumption_id=cons2.id),
    )
    # Anula la primera (más vieja)
    await InvoicesService.annul_invoice(db, org.id, inv1.id)
    await db.refresh(inv1)

    # Pago de 35,000 — debe ir a inv2, NO a inv1 anulada
    await PaymentsService.register_payment(
        db, org.id,
        PaymentCreate(
            subscriber_id=subscriber.id,
            amount=Decimal("35000"),
            payment_date=date(2026, 3, 1),
        ),
        collector_user_id=None,
    )
    await db.refresh(inv1)
    await db.refresh(inv2)

    assert inv1.status == "annulled"
    assert inv1.paid_amount == Decimal("0")
    assert inv2.status == "paid"
    assert inv2.paid_amount == Decimal("35000")
