"""Portal service — every method scopes data to the calling user's subscriber row."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.models import (
    WaterConsumption,
    WaterInvoice,
    WaterPayment,
    WaterPaymentInvoice,
    WaterSubscriber,
)
from src.apps.water.portal.schemas import (
    PortalConsumptionItem,
    PortalDashboard,
    PortalInvoiceItem,
    PortalMe,
    PortalPaymentItem,
    PortalPqrsListItem,
)
from src.apps.water.pqrs.schemas import PqrsCreate
from src.apps.water.pqrs.service import PqrsService
from src.core.exceptions import ForbiddenError, NotFoundError
from src.modules.organization.models import Organization


class PortalService:

    @staticmethod
    async def get_subscriber_for_user(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> WaterSubscriber:
        sub = await db.scalar(
            select(WaterSubscriber).where(
                WaterSubscriber.organization_id == org_id,
                WaterSubscriber.user_id == user_id,
            )
        )
        if sub is None:
            raise ForbiddenError(
                "Tu usuario no está vinculado a un suscriptor del acueducto. "
                "Pide al administrador que te invite al portal.",
            )
        return sub

    # ------------------------------------------------------------------
    # /me
    # ------------------------------------------------------------------
    @staticmethod
    async def me(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID,
    ) -> PortalMe:
        sub = await PortalService.get_subscriber_for_user(db, org_id, user_id)
        org = await db.get(Organization, org_id)
        name = (sub.business_name or f"{sub.first_name} {sub.last_name or ''}").strip()
        return PortalMe(
            subscriber_id=sub.id,
            code=sub.code,
            name=name,
            email=sub.email,
            phone=sub.phone,
            mobile=sub.mobile,
            address=sub.address,
            neighborhood=sub.neighborhood,
            stratum=sub.stratum,
            subscriber_type=sub.subscriber_type,
            status=sub.status,
            organization_id=org_id,
            organization_name=org.name if org else "",
        )

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------
    @staticmethod
    async def dashboard(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID,
    ) -> PortalDashboard:
        sub = await PortalService.get_subscriber_for_user(db, org_id, user_id)

        open_balance = await db.scalar(
            select(func.coalesce(func.sum(WaterInvoice.balance), 0)).where(
                WaterInvoice.subscriber_id == sub.id,
                WaterInvoice.status.in_(("pending", "partial", "overdue")),
            )
        ) or 0
        overdue_count = await db.scalar(
            select(func.count(WaterInvoice.id)).where(
                WaterInvoice.subscriber_id == sub.id,
                WaterInvoice.status == "overdue",
            )
        ) or 0
        pending_count = await db.scalar(
            select(func.count(WaterInvoice.id)).where(
                WaterInvoice.subscriber_id == sub.id,
                WaterInvoice.status.in_(("pending", "partial", "overdue")),
            )
        ) or 0

        last_inv = await db.scalar(
            select(func.max(WaterInvoice.issue_date)).where(
                WaterInvoice.subscriber_id == sub.id,
                WaterInvoice.status != "annulled",
            )
        )
        last_pay = await db.scalar(
            select(func.max(WaterPayment.payment_date)).where(
                WaterPayment.subscriber_id == sub.id,
            )
        )
        last_cons_row = await db.execute(
            select(
                WaterConsumption.consumption_cubic,
                WaterConsumption.period_year,
                WaterConsumption.period_month,
            )
            .where(WaterConsumption.subscriber_id == sub.id)
            .order_by(
                WaterConsumption.period_year.desc(),
                WaterConsumption.period_month.desc(),
            )
            .limit(1)
        )
        lc = last_cons_row.first()
        last_cons_cubic = lc[0] if lc else None
        last_cons_period = f"{lc[1]}-{lc[2]:02d}" if lc else None

        return PortalDashboard(
            open_balance=Decimal(str(open_balance)),
            overdue_count=int(overdue_count),
            pending_count=int(pending_count),
            last_invoice_date=last_inv,
            last_payment_date=last_pay,
            last_consumption_cubic=last_cons_cubic,
            last_consumption_period=last_cons_period,
        )

    # ------------------------------------------------------------------
    # Lists
    # ------------------------------------------------------------------
    @staticmethod
    async def invoices(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID,
    ) -> list[PortalInvoiceItem]:
        sub = await PortalService.get_subscriber_for_user(db, org_id, user_id)
        rows = await db.execute(
            select(WaterInvoice)
            .where(WaterInvoice.subscriber_id == sub.id)
            .order_by(WaterInvoice.consecutive.desc())
        )
        return [
            PortalInvoiceItem(
                id=i.id, consecutive=i.consecutive,
                period_year=i.period_year, period_month=i.period_month,
                issue_date=i.issue_date, due_date=i.due_date,
                total=i.total, paid_amount=i.paid_amount, balance=i.balance,
                status=i.status, consumption_cubic=i.consumption_cubic,
            )
            for i in rows.scalars().all()
        ]

    @staticmethod
    async def payments(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID,
    ) -> list[PortalPaymentItem]:
        sub = await PortalService.get_subscriber_for_user(db, org_id, user_id)
        invoices_count_sq = (
            select(
                WaterPaymentInvoice.payment_id,
                func.count(WaterPaymentInvoice.id).label("n"),
            )
            .group_by(WaterPaymentInvoice.payment_id)
            .subquery()
        )
        rows = await db.execute(
            select(
                WaterPayment.id, WaterPayment.payment_date, WaterPayment.amount,
                WaterPayment.method, WaterPayment.receipt_number,
                func.coalesce(invoices_count_sq.c.n, 0),
            )
            .outerjoin(invoices_count_sq, invoices_count_sq.c.payment_id == WaterPayment.id)
            .where(WaterPayment.subscriber_id == sub.id)
            .order_by(WaterPayment.payment_date.desc(), WaterPayment.created_at.desc())
        )
        return [
            PortalPaymentItem(
                id=r[0], payment_date=r[1], amount=r[2], method=r[3],
                receipt_number=r[4], invoices_count=int(r[5]),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def consumption(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID,
    ) -> list[PortalConsumptionItem]:
        sub = await PortalService.get_subscriber_for_user(db, org_id, user_id)
        rows = await db.execute(
            select(
                WaterConsumption.period_year, WaterConsumption.period_month,
                WaterConsumption.reading_date,
                WaterConsumption.previous_reading, WaterConsumption.current_reading,
                WaterConsumption.consumption_cubic,
            )
            .where(WaterConsumption.subscriber_id == sub.id)
            .order_by(
                WaterConsumption.period_year.desc(),
                WaterConsumption.period_month.desc(),
            )
        )
        return [
            PortalConsumptionItem(
                period_year=r[0], period_month=r[1], reading_date=r[2],
                previous_reading=r[3], current_reading=r[4],
                consumption_cubic=r[5],
            )
            for r in rows.all()
        ]

    # ------------------------------------------------------------------
    # PQRS
    # ------------------------------------------------------------------
    @staticmethod
    async def list_my_pqrs(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID,
    ) -> list[PortalPqrsListItem]:
        from src.apps.water.models import WaterPqrs
        sub = await PortalService.get_subscriber_for_user(db, org_id, user_id)
        rows = await db.execute(
            select(
                WaterPqrs.id, WaterPqrs.code, WaterPqrs.type, WaterPqrs.subject,
                WaterPqrs.status, WaterPqrs.created_at, WaterPqrs.responded_at,
            )
            .where(WaterPqrs.subscriber_id == sub.id)
            .order_by(WaterPqrs.created_at.desc())
        )
        return [
            PortalPqrsListItem(
                id=r[0], code=r[1], type=r[2], subject=r[3], status=r[4],
                created_at=r[5], responded_at=r[6],
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_my_pqrs(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID, pqrs_id: uuid.UUID,
    ):
        sub = await PortalService.get_subscriber_for_user(db, org_id, user_id)
        return await PqrsService.get_pqrs(db, org_id, pqrs_id, subscriber_id=sub.id)

    @staticmethod
    async def create_my_pqrs(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: PqrsCreate,
    ):
        sub = await PortalService.get_subscriber_for_user(db, org_id, user_id)
        return await PqrsService.create_pqrs(db, org_id, sub.id, data, created_by=user_id)
