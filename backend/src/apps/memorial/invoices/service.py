"""Lógica de generación de facturas para SavvyMemorial."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.contracts.service import (
    FREQUENCY_MONTHS,
    _add_months,
    _titular_display,
)
from src.apps.memorial.invoices.schemas import (
    BatchGenerateRequest,
    BatchGenerateResult,
    GenerateServiceInvoiceRequest,
)
from src.apps.memorial.models import (
    MemorialExequialContract,
    MemorialInvoice,
    MemorialService,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


def _responsible_from_contract(c: MemorialExequialContract) -> dict:
    """Snapshot del titular del contrato en el momento de facturar."""
    return {
        "responsible_name": _titular_display(c),
        "responsible_document": c.titular_document_number,
        "responsible_email": c.titular_email,
        "responsible_phone": c.titular_mobile or c.titular_phone,
        "responsible_address": c.titular_address,
    }


def _responsible_from_service(svc: MemorialService, primary: dict | None) -> dict:
    """Para servicios: usa el contacto familiar primario; si no existe,
    cae al fallecido (raro pero defensivo)."""
    if primary:
        name_parts = [primary.get("first_name", ""), primary.get("last_name", "") or ""]
        return {
            "responsible_name": " ".join(p for p in name_parts if p).strip() or "Familia",
            "responsible_document": primary.get("document_number"),
            "responsible_email": primary.get("email"),
            "responsible_phone": primary.get("mobile") or primary.get("phone"),
            "responsible_address": primary.get("address"),
        }
    return {
        "responsible_name": f"Familia {svc.deceased_first_name} {svc.deceased_last_name or ''}".strip(),
        "responsible_document": None,
        "responsible_email": None,
        "responsible_phone": None,
        "responsible_address": None,
    }


class InvoicesService:

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    async def _next_consecutive(db: AsyncSession, org_id: uuid.UUID) -> int:
        last = await db.scalar(
            select(func.coalesce(func.max(MemorialInvoice.consecutive), 0))
            .where(MemorialInvoice.organization_id == org_id)
        )
        return int(last) + 1

    # ------------------------------------------------------------------
    # Listing
    # ------------------------------------------------------------------
    @staticmethod
    async def list_invoices(
        db: AsyncSession,
        org_id: uuid.UUID,
        source_type: str | None = None,
        status: str | None = None,
        contract_id: uuid.UUID | None = None,
        service_id: uuid.UUID | None = None,
        unpaid_only: bool = False,
        limit: int = 200,
        offset: int = 0,
    ) -> list[MemorialInvoice]:
        stmt = (
            select(MemorialInvoice)
            .where(MemorialInvoice.organization_id == org_id)
            .order_by(MemorialInvoice.consecutive.desc())
            .limit(limit)
            .offset(offset)
        )
        if source_type:
            stmt = stmt.where(MemorialInvoice.source_type == source_type)
        if status:
            stmt = stmt.where(MemorialInvoice.status == status)
        if contract_id:
            stmt = stmt.where(MemorialInvoice.contract_id == contract_id)
        if service_id:
            stmt = stmt.where(MemorialInvoice.service_id == service_id)
        if unpaid_only:
            stmt = stmt.where(
                MemorialInvoice.balance > 0,
                MemorialInvoice.status != "annulled",
            )
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get_invoice(
        db: AsyncSession, org_id: uuid.UUID, invoice_id: uuid.UUID,
    ) -> MemorialInvoice:
        inv = await db.scalar(
            select(MemorialInvoice).where(
                MemorialInvoice.id == invoice_id,
                MemorialInvoice.organization_id == org_id,
            )
        )
        if inv is None:
            raise NotFoundError("Factura no encontrada.")
        return inv

    # ------------------------------------------------------------------
    # Generation: cuotas exequiales
    # ------------------------------------------------------------------
    @staticmethod
    async def batch_generate_dues(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: BatchGenerateRequest,
        actor_user_id: uuid.UUID | None,
    ) -> BatchGenerateResult:
        """Para cada contrato activo cuyo next_payment_date <= as_of_date,
        genera UNA factura por el periodo vigente y avanza next_payment_date."""
        as_of = data.as_of_date or date.today()

        rows = await db.execute(
            select(MemorialExequialContract).where(
                MemorialExequialContract.organization_id == org_id,
                MemorialExequialContract.status.in_(("active", "suspended")),
                MemorialExequialContract.next_payment_date <= as_of,
            )
        )
        contracts = list(rows.scalars().all())

        result = BatchGenerateResult(generated=0, skipped_no_fee=0)
        if not contracts:
            return result

        next_consec = await InvoicesService._next_consecutive(db, org_id)

        for c in contracts:
            fee = Decimal(c.fee_amount or 0)
            if fee <= 0:
                result.skipped_no_fee += 1
                continue
            # Calcular periodo: el cobro corresponde al periodo ENTRE la próxima
            # fecha pendiente y la siguiente. Ej: monthly + next=2026-06-01 →
            # period_start=2026-06-01, period_end=2026-07-01.
            period_start = c.next_payment_date or as_of
            period_end = _add_months(period_start, FREQUENCY_MONTHS[c.payment_frequency])
            due_date = period_start + timedelta(days=10)  # 10 días de gracia

            # Idempotencia: si ya hay factura no-anulada para este contrato + period_start,
            # el unique index la rechazará. Hacemos un check explícito para evitar el error.
            existing = await db.scalar(
                select(MemorialInvoice).where(
                    MemorialInvoice.organization_id == org_id,
                    MemorialInvoice.contract_id == c.id,
                    MemorialInvoice.period_start == period_start,
                    MemorialInvoice.status != "annulled",
                )
            )
            if existing is not None:
                # ya estaba — solo avanzar next_payment_date y seguir
                c.next_payment_date = period_end
                continue

            invoice = MemorialInvoice(
                organization_id=org_id,
                consecutive=next_consec,
                code=f"FAC-{next_consec:04d}",
                source_type="exequial_dues",
                contract_id=c.id,
                period_start=period_start,
                period_end=period_end,
                issue_date=as_of,
                due_date=due_date,
                subtotal=fee,
                total=fee,
                balance=fee,
                status="pending",
                description=f"Cuota plan exequial · {period_start.isoformat()}",
                created_by=actor_user_id,
                **_responsible_from_contract(c),
            )
            db.add(invoice)
            await db.flush()
            result.generated += 1
            result.invoice_ids.append(invoice.id)

            # Avanzar next_payment_date al siguiente periodo
            c.next_payment_date = period_end

        await db.flush()
        return result

    # ------------------------------------------------------------------
    # Generation: factura de servicio funerario
    # ------------------------------------------------------------------
    @staticmethod
    async def generate_invoice_for_service(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: GenerateServiceInvoiceRequest,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialInvoice:
        svc = await db.scalar(
            select(MemorialService).where(
                MemorialService.id == data.service_id,
                MemorialService.organization_id == org_id,
            )
        )
        if svc is None:
            raise NotFoundError("Servicio no encontrado.")
        existing = await db.scalar(
            select(MemorialInvoice).where(
                MemorialInvoice.organization_id == org_id,
                MemorialInvoice.service_id == svc.id,
                MemorialInvoice.status != "annulled",
            )
        )
        if existing is not None:
            raise ConflictError(
                f"El servicio ya tiene la factura {existing.code} generada.",
            )

        base = Decimal(svc.final_total or 0)
        if base <= 0:
            base = Decimal(svc.estimated_total or 0)
        if base <= 0:
            raise ValidationError(
                "El servicio no tiene valor final ni estimado; configúralo antes de facturar.",
            )

        from src.apps.memorial.models import MemorialServiceFamily
        primary_row = await db.scalar(
            select(MemorialServiceFamily).where(
                MemorialServiceFamily.service_id == svc.id,
                MemorialServiceFamily.organization_id == org_id,
                MemorialServiceFamily.is_primary.is_(True),
            )
        )
        primary = None
        if primary_row is not None:
            primary = {
                "first_name": primary_row.first_name,
                "last_name": primary_row.last_name,
                "document_number": primary_row.document_number,
                "email": primary_row.email,
                "mobile": primary_row.mobile,
                "phone": primary_row.phone,
                "address": primary_row.address,
            }

        today = date.today()
        due = today + timedelta(days=data.due_days)
        total = base + Decimal(data.surcharges) - Decimal(data.discounts)
        if total < 0:
            total = Decimal("0")

        next_consec = await InvoicesService._next_consecutive(db, org_id)
        invoice = MemorialInvoice(
            organization_id=org_id,
            consecutive=next_consec,
            code=f"FAC-{next_consec:04d}",
            source_type="service",
            service_id=svc.id,
            issue_date=today,
            due_date=due,
            subtotal=base,
            surcharges=Decimal(data.surcharges),
            discounts=Decimal(data.discounts),
            total=total,
            balance=total,
            status="pending" if total > 0 else "paid",
            description=data.description or f"Servicio funerario {svc.code}",
            notes=data.notes,
            created_by=actor_user_id,
            **_responsible_from_service(svc, primary),
        )
        db.add(invoice)
        await db.flush()
        return invoice

    # ------------------------------------------------------------------
    # Annul
    # ------------------------------------------------------------------
    @staticmethod
    async def annul_invoice(
        db: AsyncSession, org_id: uuid.UUID, invoice_id: uuid.UUID,
    ) -> MemorialInvoice:
        inv = await InvoicesService.get_invoice(db, org_id, invoice_id)
        if inv.status == "annulled":
            raise ConflictError("La factura ya está anulada.")
        if Decimal(inv.paid_amount or 0) > 0:
            raise ConflictError(
                "No se puede anular una factura con pagos aplicados. "
                "Reverso los pagos primero.",
            )
        inv.status = "annulled"
        inv.balance = Decimal("0")
        await db.flush()
        return inv
