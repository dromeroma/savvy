"""Business logic for water payments and invoice allocation."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.audit.service import write_audit
from src.apps.water.cash_accounts.service import CashAccountsService
from src.apps.water.models import (
    WaterCashAccount,
    WaterInvoice,
    WaterPayment,
    WaterPaymentInvoice,
    WaterSubscriber,
    WaterTreasuryMovement,
)
from src.apps.water.notifications.service import NotificationsService
from src.apps.water.payments.schemas import (
    PaymentAllocationResponse,
    PaymentCreate,
    PaymentListItem,
    PaymentResponse,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


class PaymentsService:

    @staticmethod
    async def list_payments(
        db: AsyncSession,
        org_id: uuid.UUID,
        subscriber_id: uuid.UUID | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        method: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[PaymentListItem]:
        invoices_count_sq = (
            select(
                WaterPaymentInvoice.payment_id,
                func.count(WaterPaymentInvoice.id).label("n"),
            )
            .group_by(WaterPaymentInvoice.payment_id)
            .subquery()
        )
        stmt = (
            select(
                WaterPayment.id, WaterPayment.payment_date, WaterPayment.amount,
                WaterPayment.method, WaterPayment.receipt_number, WaterPayment.reference,
                WaterPayment.subscriber_id,
                WaterSubscriber.code.label("sub_code"),
                func.coalesce(
                    WaterSubscriber.business_name,
                    func.concat(
                        WaterSubscriber.first_name, " ",
                        func.coalesce(WaterSubscriber.last_name, ""),
                    ),
                ).label("sub_name"),
                func.coalesce(invoices_count_sq.c.n, 0).label("inv_count"),
                WaterCashAccount.name.label("acc_name"),
            )
            .join(WaterSubscriber, WaterSubscriber.id == WaterPayment.subscriber_id)
            .outerjoin(invoices_count_sq, invoices_count_sq.c.payment_id == WaterPayment.id)
            .outerjoin(WaterCashAccount, WaterCashAccount.id == WaterPayment.cash_account_id)
            .where(WaterPayment.organization_id == org_id)
            .order_by(WaterPayment.payment_date.desc(), WaterPayment.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if subscriber_id is not None:
            stmt = stmt.where(WaterPayment.subscriber_id == subscriber_id)
        if method:
            stmt = stmt.where(WaterPayment.method == method)
        if date_from:
            stmt = stmt.where(WaterPayment.payment_date >= date_from)
        if date_to:
            stmt = stmt.where(WaterPayment.payment_date <= date_to)
        rows = await db.execute(stmt)
        return [
            PaymentListItem(
                id=r[0], payment_date=r[1], amount=r[2], method=r[3],
                receipt_number=r[4], reference=r[5], subscriber_id=r[6],
                subscriber_code=r[7], subscriber_name=(r[8].strip() if r[8] else ""),
                invoices_count=int(r[9]),
                cash_account_name=r[10],
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_payment(
        db: AsyncSession, org_id: uuid.UUID, payment_id: uuid.UUID,
    ) -> PaymentResponse:
        p = await db.scalar(
            select(WaterPayment).where(
                WaterPayment.id == payment_id,
                WaterPayment.organization_id == org_id,
            )
        )
        if p is None:
            raise NotFoundError("Payment not found.")
        # Load allocations
        rows = await db.execute(
            select(WaterPaymentInvoice.invoice_id, WaterInvoice.consecutive,
                   WaterPaymentInvoice.amount)
            .join(WaterInvoice, WaterInvoice.id == WaterPaymentInvoice.invoice_id)
            .where(WaterPaymentInvoice.payment_id == p.id)
        )
        allocations = [
            PaymentAllocationResponse(invoice_id=r[0], invoice_consecutive=r[1], amount=r[2])
            for r in rows.all()
        ]
        resp = PaymentResponse.model_validate(p)
        resp.allocations = allocations
        return resp

    @staticmethod
    async def register_payment(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: PaymentCreate,
        collector_user_id: uuid.UUID | None,
    ) -> PaymentResponse:
        # Validate subscriber
        subscriber = await db.scalar(
            select(WaterSubscriber).where(
                WaterSubscriber.id == data.subscriber_id,
                WaterSubscriber.organization_id == org_id,
            )
        )
        if subscriber is None:
            raise NotFoundError("Subscriber not found.")

        # If explicit allocations, validate they cover exactly the payment amount
        if data.allocations:
            alloc_sum = sum(Decimal(a.amount) for a in data.allocations)
            if alloc_sum != Decimal(data.amount):
                raise ValidationError(
                    f"La suma de allocations ({alloc_sum}) debe ser igual al monto "
                    f"del pago ({data.amount}).",
                )

        # Resolve cash account: explicit > default. None is OK (just no auto-movement).
        cash_account_id: uuid.UUID | None = data.cash_account_id
        if cash_account_id is not None:
            acc = await db.scalar(
                select(WaterCashAccount).where(
                    WaterCashAccount.id == cash_account_id,
                    WaterCashAccount.organization_id == org_id,
                )
            )
            if acc is None:
                raise NotFoundError("Cash account not found.")
        else:
            default = await CashAccountsService.get_default(db, org_id)
            cash_account_id = default.id if default else None

        payment = WaterPayment(
            organization_id=org_id,
            subscriber_id=subscriber.id,
            payment_date=data.payment_date,
            amount=Decimal(data.amount),
            method=data.method,
            receipt_number=data.receipt_number,
            reference=data.reference,
            notes=data.notes,
            collector_user_id=collector_user_id,
            cash_account_id=cash_account_id,
        )
        db.add(payment)
        await db.flush()

        # Auto-create treasury movement to keep cash account balances in sync.
        if cash_account_id is not None:
            movement = WaterTreasuryMovement(
                organization_id=org_id,
                cash_account_id=cash_account_id,
                movement_date=data.payment_date,
                type="income",
                category="water_payment",
                amount=Decimal(data.amount),
                description=(
                    f"Pago suscriptor {subscriber.code}"
                    + (f" · recibo {data.receipt_number}" if data.receipt_number else "")
                ),
                reference=data.receipt_number,
                payment_id=payment.id,
                recorded_by=collector_user_id,
            )
            db.add(movement)
            await db.flush()

        # Apply allocations
        if data.allocations:
            for a in data.allocations:
                await PaymentsService._apply_allocation(
                    db, org_id, payment, a.invoice_id, Decimal(a.amount),
                )
        else:
            # Auto-allocate to oldest unpaid invoices first
            remaining = Decimal(data.amount)
            invoices = await db.execute(
                select(WaterInvoice)
                .where(
                    WaterInvoice.organization_id == org_id,
                    WaterInvoice.subscriber_id == subscriber.id,
                    WaterInvoice.status != "annulled",
                    WaterInvoice.balance > 0,
                )
                .order_by(WaterInvoice.due_date, WaterInvoice.consecutive)
            )
            for inv in invoices.scalars().all():
                if remaining <= 0:
                    break
                pay_amt = min(remaining, Decimal(inv.balance))
                await PaymentsService._apply_allocation(
                    db, org_id, payment, inv.id, pay_amt,
                )
                remaining -= pay_amt
            # If money remained unallocated (no pending invoices or overpaid),
            # we still keep the payment row — the unallocated amount is "saldo a favor".

        # Recompute subscriber status: if no pending balance left → active
        pending = await db.scalar(
            select(func.coalesce(func.sum(WaterInvoice.balance), 0))
            .where(
                WaterInvoice.organization_id == org_id,
                WaterInvoice.subscriber_id == subscriber.id,
                WaterInvoice.status.in_(("pending", "partial", "overdue")),
            )
        ) or 0
        if Decimal(pending) <= 0 and subscriber.status in ("overdue", "suspended"):
            subscriber.status = "active"

        await db.flush()

        # Audit
        await write_audit(
            db, org_id, collector_user_id,
            action="payment.registered",
            resource_type="water_payment",
            resource_id=payment.id,
            details={
                "subscriber_code": subscriber.code,
                "amount": str(payment.amount),
                "method": payment.method,
                "receipt": payment.receipt_number,
            },
        )
        # Notify the subscriber (if linked to a user)
        if subscriber.user_id:
            await NotificationsService.emit(
                db, org_id, subscriber.user_id,
                type_="payment_received",
                title="Pago registrado",
                body=f"Recibimos tu pago de $ {payment.amount}. ¡Gracias!",
                link="/portal/water/payments",
            )

        return await PaymentsService.get_payment(db, org_id, payment.id)

    @staticmethod
    async def _apply_allocation(
        db: AsyncSession,
        org_id: uuid.UUID,
        payment: WaterPayment,
        invoice_id: uuid.UUID,
        amount: Decimal,
    ) -> None:
        inv = await db.scalar(
            select(WaterInvoice).where(
                WaterInvoice.id == invoice_id,
                WaterInvoice.organization_id == org_id,
            )
        )
        if inv is None:
            raise NotFoundError(f"Invoice {invoice_id} not found.")
        if inv.subscriber_id != payment.subscriber_id:
            raise ValidationError(
                "La factura pertenece a otro suscriptor.",
            )
        if inv.status == "annulled":
            raise ConflictError(
                f"No se puede pagar la factura #{inv.consecutive}: está anulada.",
            )
        balance = Decimal(inv.balance)
        if amount > balance:
            raise ValidationError(
                f"El monto a aplicar a la factura #{inv.consecutive} "
                f"({amount}) supera su saldo ({balance}).",
            )
        link = WaterPaymentInvoice(
            payment_id=payment.id, invoice_id=inv.id, amount=amount,
        )
        db.add(link)
        inv.paid_amount = Decimal(inv.paid_amount) + amount
        inv.balance = Decimal(inv.total) - Decimal(inv.paid_amount)
        if inv.balance <= 0:
            inv.status = "paid"
        elif inv.paid_amount > 0:
            inv.status = "partial"
        await db.flush()
