"""Billing engine + invoice management for SavvyWater."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.invoices.schemas import (
    BatchGenerateRequest,
    BatchGenerateResult,
    GenerateInvoiceRequest,
    InvoiceListItem,
)
from src.apps.water.models import (
    WaterConsumption,
    WaterInvoice,
    WaterSubscriber,
    WaterTariff,
)
from src.apps.water.tariffs.service import TariffsService
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


DEFAULT_DUE_DAYS = 15


class InvoicesService:

    # ------------------------------------------------------------------
    # Listing / detail
    # ------------------------------------------------------------------
    @staticmethod
    async def list_invoices(
        db: AsyncSession,
        org_id: uuid.UUID,
        status: str | None = None,
        period_year: int | None = None,
        period_month: int | None = None,
        subscriber_id: uuid.UUID | None = None,
        unpaid_only: bool = False,
        limit: int = 200,
        offset: int = 0,
    ) -> list[InvoiceListItem]:
        stmt = (
            select(
                WaterInvoice.id, WaterInvoice.consecutive,
                WaterInvoice.period_year, WaterInvoice.period_month,
                WaterInvoice.issue_date, WaterInvoice.due_date,
                WaterInvoice.total, WaterInvoice.paid_amount, WaterInvoice.balance,
                WaterInvoice.status, WaterInvoice.subscriber_id,
                WaterSubscriber.code.label("sub_code"),
                func.coalesce(
                    WaterSubscriber.business_name,
                    func.concat(
                        WaterSubscriber.first_name, " ",
                        func.coalesce(WaterSubscriber.last_name, ""),
                    ),
                ).label("sub_name"),
            )
            .join(WaterSubscriber, WaterSubscriber.id == WaterInvoice.subscriber_id)
            .where(WaterInvoice.organization_id == org_id)
            .order_by(WaterInvoice.consecutive.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            stmt = stmt.where(WaterInvoice.status == status)
        if period_year is not None:
            stmt = stmt.where(WaterInvoice.period_year == period_year)
        if period_month is not None:
            stmt = stmt.where(WaterInvoice.period_month == period_month)
        if subscriber_id is not None:
            stmt = stmt.where(WaterInvoice.subscriber_id == subscriber_id)
        if unpaid_only:
            stmt = stmt.where(WaterInvoice.balance > 0).where(
                WaterInvoice.status != "annulled",
            )
        rows = await db.execute(stmt)
        return [
            InvoiceListItem(
                id=r[0], consecutive=r[1], period_year=r[2], period_month=r[3],
                issue_date=r[4], due_date=r[5], total=r[6], paid_amount=r[7],
                balance=r[8], status=r[9], subscriber_id=r[10],
                subscriber_code=r[11], subscriber_name=(r[12].strip() if r[12] else ""),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_invoice(
        db: AsyncSession, org_id: uuid.UUID, invoice_id: uuid.UUID,
    ) -> WaterInvoice:
        inv = await db.scalar(
            select(WaterInvoice).where(
                WaterInvoice.id == invoice_id,
                WaterInvoice.organization_id == org_id,
            )
        )
        if inv is None:
            raise NotFoundError("Invoice not found.")
        return inv

    # ------------------------------------------------------------------
    # Generation (single)
    # ------------------------------------------------------------------
    @staticmethod
    async def generate_from_consumption(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: GenerateInvoiceRequest,
    ) -> WaterInvoice:
        cons = await db.scalar(
            select(WaterConsumption).where(
                WaterConsumption.id == data.consumption_id,
                WaterConsumption.organization_id == org_id,
            )
        )
        if cons is None:
            raise NotFoundError("Consumption reading not found.")

        # Already invoiced?
        existing = await db.scalar(
            select(WaterInvoice).where(
                WaterInvoice.consumption_id == cons.id,
                WaterInvoice.status != "annulled",
            )
        )
        if existing is not None:
            raise ConflictError(
                f"Esta lectura ya tiene la factura #{existing.consecutive} generada.",
            )

        subscriber = await db.scalar(
            select(WaterSubscriber).where(WaterSubscriber.id == cons.subscriber_id),
        )
        if subscriber is None:
            raise NotFoundError("Subscriber not found.")

        issue_date = data.issue_date or date.today()
        due_date = data.due_date or (issue_date + timedelta(days=DEFAULT_DUE_DAYS))

        tariff = await TariffsService.resolve_for_subscriber(
            db, org_id,
            subscriber_type=subscriber.subscriber_type,
            stratum=subscriber.stratum,
            on_date=issue_date,
        )
        if tariff is None:
            raise ValidationError(
                f"No hay tarifa configurada para suscriptor tipo "
                f"'{subscriber.subscriber_type}' "
                f"estrato {subscriber.stratum or 'N/A'} en {issue_date}.",
            )

        invoice = InvoicesService._build_invoice(
            org_id=org_id, subscriber=subscriber, cons=cons, tariff=tariff,
            issue_date=issue_date, due_date=due_date,
            surcharges=data.surcharges, discounts=data.discounts,
            notes=data.notes,
        )
        invoice.consecutive = await InvoicesService._next_consecutive(db, org_id)
        db.add(invoice)
        await db.flush()
        await db.refresh(invoice)
        return invoice

    # ------------------------------------------------------------------
    # Batch generation (per period)
    # ------------------------------------------------------------------
    @staticmethod
    async def batch_generate(
        db: AsyncSession, org_id: uuid.UUID, data: BatchGenerateRequest,
    ) -> BatchGenerateResult:
        issue_date = data.issue_date or date.today()
        due_date = data.due_date or (issue_date + timedelta(days=DEFAULT_DUE_DAYS))

        # Consumptions in period that don't have an invoice yet
        rows = await db.execute(
            select(WaterConsumption, WaterSubscriber)
            .join(WaterSubscriber, WaterSubscriber.id == WaterConsumption.subscriber_id)
            .outerjoin(
                WaterInvoice,
                (WaterInvoice.consumption_id == WaterConsumption.id)
                & (WaterInvoice.status != "annulled"),
            )
            .where(
                WaterConsumption.organization_id == org_id,
                WaterConsumption.period_year == data.period_year,
                WaterConsumption.period_month == data.period_month,
                WaterInvoice.id.is_(None),
            )
        )
        candidates = rows.all()

        result = BatchGenerateResult(
            generated=0, skipped_existing=0, skipped_no_tariff=0, errors=[],
        )
        if not candidates:
            return result

        # Cache tariff resolution per (subscriber_type, stratum) for speed
        tariff_cache: dict[tuple[str, int | None], WaterTariff | None] = {}
        next_consec = await InvoicesService._next_consecutive(db, org_id)

        for cons, subscriber in candidates:
            key = (subscriber.subscriber_type, subscriber.stratum)
            if key not in tariff_cache:
                tariff_cache[key] = await TariffsService.resolve_for_subscriber(
                    db, org_id,
                    subscriber_type=subscriber.subscriber_type,
                    stratum=subscriber.stratum,
                    on_date=issue_date,
                )
            tariff = tariff_cache[key]
            if tariff is None:
                result.skipped_no_tariff += 1
                result.errors.append(
                    f"{subscriber.code}: no hay tarifa para "
                    f"{subscriber.subscriber_type}/{subscriber.stratum or 'N/A'}",
                )
                continue

            invoice = InvoicesService._build_invoice(
                org_id=org_id, subscriber=subscriber, cons=cons, tariff=tariff,
                issue_date=issue_date, due_date=due_date,
            )
            invoice.consecutive = next_consec
            next_consec += 1
            db.add(invoice)
            result.generated += 1
            result.invoice_ids.append(invoice.id)

        await db.flush()
        return result

    # ------------------------------------------------------------------
    # Annulment
    # ------------------------------------------------------------------
    @staticmethod
    async def annul_invoice(
        db: AsyncSession, org_id: uuid.UUID, invoice_id: uuid.UUID,
    ) -> WaterInvoice:
        inv = await InvoicesService.get_invoice(db, org_id, invoice_id)
        if inv.status == "annulled":
            raise ConflictError("La factura ya está anulada.")
        if inv.paid_amount and Decimal(inv.paid_amount) > 0:
            raise ConflictError(
                "No se puede anular una factura con pagos aplicados. "
                "Anula primero los pagos.",
            )
        inv.status = "annulled"
        inv.balance = Decimal("0")
        await db.flush()
        await db.refresh(inv)
        return inv

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    @staticmethod
    async def _next_consecutive(db: AsyncSession, org_id: uuid.UUID) -> int:
        last = await db.scalar(
            select(func.coalesce(func.max(WaterInvoice.consecutive), 0))
            .where(WaterInvoice.organization_id == org_id)
        )
        return int(last) + 1

    @staticmethod
    def _build_invoice(
        *,
        org_id: uuid.UUID,
        subscriber: WaterSubscriber,
        cons: WaterConsumption,
        tariff: WaterTariff,
        issue_date: date,
        due_date: date,
        surcharges: Decimal = Decimal("0"),
        discounts: Decimal = Decimal("0"),
        notes: str | None = None,
    ) -> WaterInvoice:
        """Compose a WaterInvoice from a reading + tariff. Does NOT add to db."""
        cubic = Decimal(cons.consumption_cubic)
        fixed = Decimal(tariff.fixed_charge or 0)

        # Consumption charge with optional basic-limit tier
        if tariff.basic_limit_cubic and tariff.surplus_price_per_cubic is not None:
            basic_limit = Decimal(tariff.basic_limit_cubic)
            basic_qty = min(cubic, basic_limit)
            surplus_qty = max(Decimal("0"), cubic - basic_limit)
            consumption_charge = (
                basic_qty * Decimal(tariff.price_per_cubic)
                + surplus_qty * Decimal(tariff.surplus_price_per_cubic)
            )
        else:
            consumption_charge = cubic * Decimal(tariff.price_per_cubic)

        total = (
            fixed + consumption_charge + Decimal(surcharges) - Decimal(discounts)
        )
        if total < 0:
            total = Decimal("0")

        return WaterInvoice(
            organization_id=org_id,
            subscriber_id=subscriber.id,
            consumption_id=cons.id,
            period_year=cons.period_year,
            period_month=cons.period_month,
            issue_date=issue_date,
            due_date=due_date,
            fixed_charge=fixed,
            consumption_cubic=cubic,
            consumption_charge=consumption_charge,
            late_interest=Decimal("0"),  # cartera/mora se calcula en fase 3
            surcharges=Decimal(surcharges),
            discounts=Decimal(discounts),
            reconnection_fee=Decimal("0"),
            suspension_fee=Decimal("0"),
            total=total,
            paid_amount=Decimal("0"),
            balance=total,
            status="pending",
            notes=notes,
        )
