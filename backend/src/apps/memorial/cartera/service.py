"""Cartera de SavvyMemorial: mora compuesta idempotente + aging + lista
de morosos + suspensión automática del contrato tras N cuotas vencidas."""

from __future__ import annotations

import math
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.cartera.schemas import (
    AgingBucket,
    AgingReport,
    OverdueDebtor,
    RecalcResult,
)
from src.apps.memorial.models import (
    MemorialExequialContract,
    MemorialInvoice,
    MemorialService,
)


# Si un contrato acumula N cuotas vencidas sin pagar → suspensión automática.
OVERDUE_SUSPENSION_THRESHOLD = 3

# Tasa de interés mensual aplicada por defecto a cuotas vencidas.
# Si más adelante se quiere por plan, agregar columna late_interest_rate al plan.
DEFAULT_LATE_INTEREST_RATE = Decimal("0.02")


class CarteraService:

    @staticmethod
    async def recalc_overdue(
        db: AsyncSession,
        org_id: uuid.UUID,
        on_date: date | None = None,
        rate: Decimal | None = None,
    ) -> RecalcResult:
        """Marca facturas vencidas, aplica interés compuesto idempotente
        (months_overdue * rate * base, donde base = total - late_interest_ya_aplicado),
        y suspende contratos con demasiadas cuotas vencidas."""
        today = on_date or date.today()
        r = rate if rate is not None else DEFAULT_LATE_INTEREST_RATE

        result = RecalcResult(
            invoices_marked_overdue=0,
            invoices_with_interest_applied=0,
            contracts_suspended=0,
            total_interest_applied=Decimal("0"),
        )

        # Recompute por factura
        invoices = (await db.execute(
            select(MemorialInvoice).where(
                MemorialInvoice.organization_id == org_id,
                MemorialInvoice.status.in_(("pending", "partial", "overdue")),
                MemorialInvoice.due_date < today,
            )
        )).scalars().all()

        for inv in invoices:
            if inv.status != "overdue":
                inv.status = "overdue"
                result.invoices_marked_overdue += 1
            if r <= 0:
                continue
            days_overdue = (today - inv.due_date).days
            if days_overdue <= 0:
                continue
            months_overdue = math.ceil(days_overdue / 30)
            base = Decimal(inv.total) - Decimal(inv.late_interest)
            new_interest = (base * r * Decimal(months_overdue)).quantize(Decimal("0.01"))
            if new_interest <= Decimal(inv.late_interest):
                continue
            diff = new_interest - Decimal(inv.late_interest)
            inv.late_interest = new_interest
            inv.total = base + new_interest
            inv.balance = Decimal(inv.total) - Decimal(inv.paid_amount)
            result.invoices_with_interest_applied += 1
            result.total_interest_applied += diff

        # Suspensión automática de contratos con N cuotas vencidas
        overdue_count_sq = (
            select(
                MemorialInvoice.contract_id,
                func.count(MemorialInvoice.id).label("n"),
            )
            .where(
                MemorialInvoice.organization_id == org_id,
                MemorialInvoice.status == "overdue",
                MemorialInvoice.contract_id.is_not(None),
            )
            .group_by(MemorialInvoice.contract_id)
            .subquery()
        )
        rows = await db.execute(
            select(MemorialExequialContract, overdue_count_sq.c.n)
            .join(
                overdue_count_sq,
                overdue_count_sq.c.contract_id == MemorialExequialContract.id,
            )
            .where(
                MemorialExequialContract.organization_id == org_id,
                MemorialExequialContract.status == "active",
                overdue_count_sq.c.n >= OVERDUE_SUSPENSION_THRESHOLD,
            )
        )
        for contract, n in rows.all():
            contract.status = "suspended"
            contract.suspended_at = datetime.now(UTC)
            result.contracts_suspended += 1

        await db.flush()
        return result

    @staticmethod
    async def aging_report(
        db: AsyncSession,
        org_id: uuid.UUID,
        on_date: date | None = None,
    ) -> AgingReport:
        today = on_date or date.today()
        days = func.greatest(0, today - MemorialInvoice.due_date)
        bucket = case(
            (days <= 0, "current"),
            (days <= 30, "0_30"),
            (days <= 60, "31_60"),
            (days <= 90, "61_90"),
            else_="90_plus",
        )
        rows = await db.execute(
            select(
                bucket.label("b"),
                func.count(MemorialInvoice.id),
                func.coalesce(func.sum(MemorialInvoice.balance), 0),
            )
            .where(
                MemorialInvoice.organization_id == org_id,
                MemorialInvoice.status.in_(("pending", "partial", "overdue")),
                MemorialInvoice.balance > 0,
            )
            .group_by("b")
        )
        by_bucket: dict[str, tuple[int, Decimal]] = {}
        for r in rows.all():
            by_bucket[r[0]] = (int(r[1]), Decimal(str(r[2])))
        ordered_keys = ["current", "0_30", "31_60", "61_90", "90_plus"]
        buckets = [
            AgingBucket(
                bucket=k,
                invoices=by_bucket.get(k, (0, Decimal("0")))[0],
                balance=by_bucket.get(k, (0, Decimal("0")))[1],
            )
            for k in ordered_keys
        ]
        total = sum((b.balance for b in buckets), start=Decimal("0"))
        return AgingReport(total_balance=total, buckets=buckets)

    @staticmethod
    async def overdue_debtors(
        db: AsyncSession,
        org_id: uuid.UUID,
        limit: int = 100,
        on_date: date | None = None,
    ) -> list[OverdueDebtor]:
        """Lista de morosos. Agrupa facturas vencidas por contrato (cuando
        existe contract_id) o por servicio (cuando es servicio funerario)."""
        today = on_date or date.today()

        # Por contrato
        rows = await db.execute(
            select(
                MemorialExequialContract.id,
                MemorialExequialContract.code,
                MemorialExequialContract.titular_first_name,
                MemorialExequialContract.titular_last_name,
                MemorialExequialContract.titular_business_name,
                MemorialExequialContract.titular_email,
                func.coalesce(
                    MemorialExequialContract.titular_mobile,
                    MemorialExequialContract.titular_phone,
                ).label("phone"),
                func.count(MemorialInvoice.id).label("n"),
                func.min(MemorialInvoice.due_date).label("oldest"),
                func.coalesce(func.sum(MemorialInvoice.balance), 0).label("bal"),
            )
            .join(MemorialInvoice, MemorialInvoice.contract_id == MemorialExequialContract.id)
            .where(
                MemorialExequialContract.organization_id == org_id,
                MemorialInvoice.status.in_(("overdue", "partial")),
                MemorialInvoice.balance > 0,
                MemorialInvoice.due_date < today,
            )
            .group_by(
                MemorialExequialContract.id,
                MemorialExequialContract.code,
                MemorialExequialContract.titular_first_name,
                MemorialExequialContract.titular_last_name,
                MemorialExequialContract.titular_business_name,
                MemorialExequialContract.titular_email,
                MemorialExequialContract.titular_mobile,
                MemorialExequialContract.titular_phone,
            )
            .order_by(func.min(MemorialInvoice.due_date))
            .limit(limit)
        )
        debtors: list[OverdueDebtor] = []
        for r in rows.all():
            name = (
                r[4] if r[4]
                else f"{r[2] or ''} {r[3] or ''}".strip() or "(sin nombre)"
            )
            oldest = r[8]
            debtors.append(OverdueDebtor(
                contract_id=r[0], service_id=None,
                code=r[1], name=name,
                phone=r[6], email=r[5],
                overdue_invoices=int(r[7]),
                oldest_due_date=oldest.isoformat() if oldest else None,
                days_overdue=(today - oldest).days if oldest else 0,
                total_balance=Decimal(str(r[9])),
            ))

        # Por servicio (sin contrato)
        rows2 = await db.execute(
            select(
                MemorialService.id,
                MemorialService.code,
                MemorialService.deceased_first_name,
                MemorialService.deceased_last_name,
                func.count(MemorialInvoice.id).label("n"),
                func.min(MemorialInvoice.due_date).label("oldest"),
                func.coalesce(func.sum(MemorialInvoice.balance), 0).label("bal"),
            )
            .join(MemorialInvoice, MemorialInvoice.service_id == MemorialService.id)
            .where(
                MemorialService.organization_id == org_id,
                MemorialInvoice.contract_id.is_(None),
                MemorialInvoice.status.in_(("overdue", "partial")),
                MemorialInvoice.balance > 0,
                MemorialInvoice.due_date < today,
            )
            .group_by(
                MemorialService.id,
                MemorialService.code,
                MemorialService.deceased_first_name,
                MemorialService.deceased_last_name,
            )
            .order_by(func.min(MemorialInvoice.due_date))
            .limit(limit)
        )
        for r in rows2.all():
            name = f"Familia {r[2]} {r[3] or ''}".strip()
            oldest = r[5]
            debtors.append(OverdueDebtor(
                contract_id=None, service_id=r[0],
                code=r[1], name=name,
                phone=None, email=None,
                overdue_invoices=int(r[4]),
                oldest_due_date=oldest.isoformat() if oldest else None,
                days_overdue=(today - oldest).days if oldest else 0,
                total_balance=Decimal(str(r[6])),
            ))

        debtors.sort(key=lambda d: -d.days_overdue)
        return debtors[:limit]
