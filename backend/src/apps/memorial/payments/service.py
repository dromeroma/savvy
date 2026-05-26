"""Lógica de pagos para SavvyMemorial — FIFO allocation."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.models import (
    MemorialExequialContract,
    MemorialInvoice,
    MemorialPayment,
    MemorialPaymentInvoice,
    MemorialService,
)
from src.apps.memorial.payments.schemas import (
    PaymentCreate,
    PaymentListItem,
    PaymentResponse,
    PaymentAllocationResponse,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


class PaymentsService:

    @staticmethod
    async def _next_consecutive(db: AsyncSession, org_id: uuid.UUID) -> int:
        last = await db.scalar(
            select(func.coalesce(func.max(MemorialPayment.consecutive), 0))
            .where(MemorialPayment.organization_id == org_id)
        )
        return int(last) + 1

    @staticmethod
    async def list_payments(
        db: AsyncSession,
        org_id: uuid.UUID,
        contract_id: uuid.UUID | None = None,
        service_id: uuid.UUID | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        method: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[PaymentListItem]:
        invoices_count_sq = (
            select(
                MemorialPaymentInvoice.payment_id,
                func.count(MemorialPaymentInvoice.id).label("n"),
            )
            .group_by(MemorialPaymentInvoice.payment_id)
            .subquery()
        )
        stmt = (
            select(
                MemorialPayment.id, MemorialPayment.code, MemorialPayment.consecutive,
                MemorialPayment.payment_date, MemorialPayment.amount,
                MemorialPayment.method, MemorialPayment.receipt_number,
                MemorialPayment.payer_name,
                MemorialPayment.contract_id, MemorialPayment.service_id,
                func.coalesce(invoices_count_sq.c.n, 0).label("n"),
            )
            .outerjoin(invoices_count_sq, invoices_count_sq.c.payment_id == MemorialPayment.id)
            .where(MemorialPayment.organization_id == org_id)
            .order_by(MemorialPayment.consecutive.desc())
            .limit(limit).offset(offset)
        )
        if contract_id:
            stmt = stmt.where(MemorialPayment.contract_id == contract_id)
        if service_id:
            stmt = stmt.where(MemorialPayment.service_id == service_id)
        if method:
            stmt = stmt.where(MemorialPayment.method == method)
        if date_from:
            stmt = stmt.where(MemorialPayment.payment_date >= date_from)
        if date_to:
            stmt = stmt.where(MemorialPayment.payment_date <= date_to)
        rows = await db.execute(stmt)
        return [
            PaymentListItem(
                id=r[0], code=r[1], consecutive=r[2],
                payment_date=r[3], amount=r[4], method=r[5],
                receipt_number=r[6], payer_name=r[7],
                contract_id=r[8], service_id=r[9],
                invoices_count=int(r[10]),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_payment(
        db: AsyncSession, org_id: uuid.UUID, payment_id: uuid.UUID,
    ) -> PaymentResponse:
        p = await db.scalar(
            select(MemorialPayment).where(
                MemorialPayment.id == payment_id,
                MemorialPayment.organization_id == org_id,
            )
        )
        if p is None:
            raise NotFoundError("Pago no encontrado.")
        rows = await db.execute(
            select(
                MemorialPaymentInvoice.invoice_id,
                MemorialInvoice.code,
                MemorialPaymentInvoice.amount,
            )
            .join(MemorialInvoice, MemorialInvoice.id == MemorialPaymentInvoice.invoice_id)
            .where(MemorialPaymentInvoice.payment_id == p.id)
        )
        allocations = [
            PaymentAllocationResponse(invoice_id=r[0], invoice_code=r[1], amount=r[2])
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
        actor_user_id: uuid.UUID | None,
    ) -> PaymentResponse:
        if not data.contract_id and not data.service_id:
            raise ValidationError(
                "Indica un contrato o un servicio asociado al pago.",
            )

        # Validar el origen
        if data.contract_id:
            c = await db.scalar(
                select(MemorialExequialContract).where(
                    MemorialExequialContract.id == data.contract_id,
                    MemorialExequialContract.organization_id == org_id,
                )
            )
            if c is None:
                raise NotFoundError("Contrato no encontrado.")
        if data.service_id:
            s = await db.scalar(
                select(MemorialService).where(
                    MemorialService.id == data.service_id,
                    MemorialService.organization_id == org_id,
                )
            )
            if s is None:
                raise NotFoundError("Servicio no encontrado.")

        if data.allocations:
            alloc_sum = sum(Decimal(a.amount) for a in data.allocations)
            if alloc_sum != Decimal(data.amount):
                raise ValidationError(
                    f"La suma de allocations ({alloc_sum}) debe ser igual al "
                    f"monto del pago ({data.amount}).",
                )

        consec = await PaymentsService._next_consecutive(db, org_id)
        payment = MemorialPayment(
            organization_id=org_id,
            consecutive=consec,
            code=f"REC-{consec:04d}",
            contract_id=data.contract_id,
            service_id=data.service_id,
            payer_name=data.payer_name,
            payer_document=data.payer_document,
            payer_email=data.payer_email,
            payer_phone=data.payer_phone,
            payment_date=data.payment_date,
            amount=Decimal(data.amount),
            method=data.method,
            receipt_number=data.receipt_number,
            reference=data.reference,
            notes=data.notes,
            recorded_by=actor_user_id,
        )
        db.add(payment)
        await db.flush()

        # Aplicar allocations
        if data.allocations:
            for a in data.allocations:
                await PaymentsService._apply(
                    db, org_id, payment, a.invoice_id, Decimal(a.amount),
                )
        else:
            # FIFO contra las facturas pendientes del mismo contrato o servicio
            stmt = select(MemorialInvoice).where(
                MemorialInvoice.organization_id == org_id,
                MemorialInvoice.status != "annulled",
                MemorialInvoice.balance > 0,
            )
            if data.contract_id:
                stmt = stmt.where(MemorialInvoice.contract_id == data.contract_id)
            elif data.service_id:
                stmt = stmt.where(MemorialInvoice.service_id == data.service_id)
            stmt = stmt.order_by(MemorialInvoice.due_date, MemorialInvoice.consecutive)
            invoices = (await db.execute(stmt)).scalars().all()
            remaining = Decimal(data.amount)
            for inv in invoices:
                if remaining <= 0:
                    break
                pay_amt = min(remaining, Decimal(inv.balance))
                await PaymentsService._apply(db, org_id, payment, inv.id, pay_amt)
                remaining -= pay_amt
            # Si quedó sobrante (sin facturas) → queda como saldo a favor en el pago

        await db.flush()
        return await PaymentsService.get_payment(db, org_id, payment.id)

    @staticmethod
    async def _apply(
        db: AsyncSession,
        org_id: uuid.UUID,
        payment: MemorialPayment,
        invoice_id: uuid.UUID,
        amount: Decimal,
    ) -> None:
        inv = await db.scalar(
            select(MemorialInvoice).where(
                MemorialInvoice.id == invoice_id,
                MemorialInvoice.organization_id == org_id,
            )
        )
        if inv is None:
            raise NotFoundError(f"Factura {invoice_id} no encontrada.")
        if inv.status == "annulled":
            raise ConflictError(
                f"No se puede pagar la factura {inv.code}: está anulada.",
            )
        balance = Decimal(inv.balance)
        if amount > balance:
            raise ValidationError(
                f"El monto a aplicar a la factura {inv.code} ({amount}) "
                f"supera su saldo ({balance}).",
            )
        link = MemorialPaymentInvoice(
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
