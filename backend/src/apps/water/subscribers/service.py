"""Business logic for water subscribers."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.models import WaterInvoice, WaterMeter, WaterSubscriber
from src.apps.water.subscribers.schemas import (
    InvitePortalRequest,
    InvitePortalResponse,
    SubscriberCreate,
    SubscriberListItem,
    SubscriberUpdate,
)
from src.apps.water.tariffs.service import TariffsService
from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.core.security import hash_password
from src.modules.apps.models import AppRegistry, AppUserRole
from src.modules.auth.models import User
from src.modules.organization.models import Membership


class SubscribersService:

    @staticmethod
    async def list_subscribers(
        db: AsyncSession,
        org_id: uuid.UUID,
        search: str | None = None,
        status: str | None = None,
        subscriber_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SubscriberListItem]:
        meter_count_sq = (
            select(
                WaterMeter.subscriber_id,
                func.count(WaterMeter.id).label("n"),
            )
            .where(WaterMeter.organization_id == org_id)
            .group_by(WaterMeter.subscriber_id)
            .subquery()
        )

        stmt = (
            select(
                WaterSubscriber.id,
                WaterSubscriber.code,
                WaterSubscriber.first_name,
                WaterSubscriber.last_name,
                WaterSubscriber.business_name,
                WaterSubscriber.document_number,
                WaterSubscriber.address,
                WaterSubscriber.neighborhood,
                WaterSubscriber.subscriber_type,
                WaterSubscriber.status,
                WaterSubscriber.stratum,
                func.coalesce(meter_count_sq.c.n, 0).label("meter_count"),
            )
            .outerjoin(meter_count_sq, meter_count_sq.c.subscriber_id == WaterSubscriber.id)
            .where(WaterSubscriber.organization_id == org_id)
            .order_by(WaterSubscriber.code)
            .limit(limit)
            .offset(offset)
        )
        if status:
            stmt = stmt.where(WaterSubscriber.status == status)
        if subscriber_type:
            stmt = stmt.where(WaterSubscriber.subscriber_type == subscriber_type)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(WaterSubscriber.code).like(like),
                    func.lower(WaterSubscriber.first_name).like(like),
                    func.lower(func.coalesce(WaterSubscriber.last_name, "")).like(like),
                    func.lower(func.coalesce(WaterSubscriber.business_name, "")).like(like),
                    func.lower(func.coalesce(WaterSubscriber.document_number, "")).like(like),
                )
            )

        rows = await db.execute(stmt)
        return [
            SubscriberListItem(
                id=r[0], code=r[1], first_name=r[2], last_name=r[3],
                business_name=r[4], document_number=r[5], address=r[6],
                neighborhood=r[7], subscriber_type=r[8], status=r[9],
                stratum=r[10], meter_count=int(r[11]),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_subscriber(
        db: AsyncSession, org_id: uuid.UUID, sub_id: uuid.UUID,
    ) -> WaterSubscriber:
        sub = await db.scalar(
            select(WaterSubscriber).where(
                WaterSubscriber.id == sub_id,
                WaterSubscriber.organization_id == org_id,
            )
        )
        if sub is None:
            raise NotFoundError("Subscriber not found.")
        return sub

    @staticmethod
    async def create_subscriber(
        db: AsyncSession, org_id: uuid.UUID, data: SubscriberCreate,
    ) -> WaterSubscriber:
        existing = await db.scalar(
            select(WaterSubscriber).where(
                WaterSubscriber.organization_id == org_id,
                WaterSubscriber.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Already exists a subscriber with code '{data.code}'.")
        sub = WaterSubscriber(organization_id=org_id, **data.model_dump())
        db.add(sub)
        await db.flush()
        await db.refresh(sub)
        return sub

    @staticmethod
    async def update_subscriber(
        db: AsyncSession,
        org_id: uuid.UUID,
        sub_id: uuid.UUID,
        data: SubscriberUpdate,
    ) -> WaterSubscriber:
        sub = await SubscribersService.get_subscriber(db, org_id, sub_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(sub, k, v)
        await db.flush()
        await db.refresh(sub)
        return sub

    @staticmethod
    async def delete_subscriber(
        db: AsyncSession, org_id: uuid.UUID, sub_id: uuid.UUID,
    ) -> None:
        sub = await SubscribersService.get_subscriber(db, org_id, sub_id)
        await db.delete(sub)
        await db.flush()

    # ------------------------------------------------------------------
    # Service actions: suspend & reconnect
    # ------------------------------------------------------------------
    @staticmethod
    async def suspend(
        db: AsyncSession,
        org_id: uuid.UUID,
        sub_id: uuid.UUID,
        reason: str | None = None,
        create_fee_invoice: bool = True,
    ) -> WaterSubscriber:
        sub = await SubscribersService.get_subscriber(db, org_id, sub_id)
        if sub.status == "suspended":
            raise ConflictError("El suscriptor ya está suspendido.")
        if sub.status == "retired":
            raise ConflictError("No se puede suspender un suscriptor retirado.")
        sub.status = "suspended"
        await db.flush()
        if create_fee_invoice:
            await SubscribersService._create_fee_invoice(
                db, org_id, sub, kind="suspension", notes=reason,
            )
        return sub

    @staticmethod
    async def reconnect(
        db: AsyncSession,
        org_id: uuid.UUID,
        sub_id: uuid.UUID,
        reason: str | None = None,
        create_fee_invoice: bool = True,
    ) -> WaterSubscriber:
        sub = await SubscribersService.get_subscriber(db, org_id, sub_id)
        if sub.status != "suspended":
            raise ConflictError(
                "Solo se puede reconectar un suscriptor suspendido.",
            )
        sub.status = "active"
        await db.flush()
        if create_fee_invoice:
            await SubscribersService._create_fee_invoice(
                db, org_id, sub, kind="reconnection", notes=reason,
            )
        return sub

    @staticmethod
    async def _create_fee_invoice(
        db: AsyncSession,
        org_id: uuid.UUID,
        sub: WaterSubscriber,
        kind: str,            # 'suspension' | 'reconnection'
        notes: str | None = None,
    ) -> WaterInvoice | None:
        """Create an adjustment invoice (no consumption) with the suspension
        or reconnection fee from the applicable tariff. Returns None if the
        tariff doesn't define a fee."""
        today = date.today()
        tariff = await TariffsService.resolve_for_subscriber(
            db, org_id,
            subscriber_type=sub.subscriber_type, stratum=sub.stratum,
            on_date=today,
        )
        if tariff is None:
            raise ValidationError(
                "No hay tarifa configurada para este suscriptor — no se puede generar la factura de ajuste.",
            )
        fee = Decimal(
            tariff.suspension_fee if kind == "suspension" else tariff.reconnection_fee,
        )
        if fee <= 0:
            return None
        consec = await db.scalar(
            select(func.coalesce(func.max(WaterInvoice.consecutive), 0))
            .where(WaterInvoice.organization_id == org_id)
        )
        inv = WaterInvoice(
            organization_id=org_id,
            subscriber_id=sub.id,
            consumption_id=None,
            consecutive=int(consec) + 1,
            period_year=today.year,
            period_month=today.month,
            issue_date=today,
            due_date=today + timedelta(days=15),
            fixed_charge=Decimal("0"),
            consumption_cubic=Decimal("0"),
            consumption_charge=Decimal("0"),
            late_interest=Decimal("0"),
            surcharges=Decimal("0"),
            discounts=Decimal("0"),
            reconnection_fee=fee if kind == "reconnection" else Decimal("0"),
            suspension_fee=fee if kind == "suspension" else Decimal("0"),
            total=fee,
            paid_amount=Decimal("0"),
            balance=fee,
            status="pending",
            notes=notes or (
                "Factura de ajuste por suspensión" if kind == "suspension"
                else "Factura de ajuste por reconexión"
            ),
        )
        db.add(inv)
        await db.flush()
        return inv

    # ------------------------------------------------------------------
    # Portal invitation
    # ------------------------------------------------------------------
    @staticmethod
    async def invite_portal(
        db: AsyncSession,
        org_id: uuid.UUID,
        sub_id: uuid.UUID,
        data: InvitePortalRequest,
    ) -> InvitePortalResponse:
        """Link a subscriber to a Savvy user with the 'customer' role on
        the water app, so they can log into the portal."""
        sub = await SubscribersService.get_subscriber(db, org_id, sub_id)
        if sub.user_id is not None:
            existing = await db.get(User, sub.user_id)
            if existing is not None:
                raise ConflictError(
                    f"Este suscriptor ya está vinculado al usuario {existing.email}.",
                )

        email = data.email.lower().strip()
        # Re-use existing user if email matches; otherwise create one.
        user = await db.scalar(select(User).where(User.email == email))
        created_new_user = False
        if user is None:
            display_name = (
                data.name
                or sub.business_name
                or f"{sub.first_name} {sub.last_name or ''}".strip()
            )
            user = User(
                name=display_name,
                email=email,
                password_hash=hash_password(data.password),
            )
            db.add(user)
            await db.flush()
            created_new_user = True

        # Org membership: needed so the JWT carries org_id at login.
        membership = await db.scalar(
            select(Membership).where(
                Membership.organization_id == org_id,
                Membership.user_id == user.id,
            )
        )
        if membership is None:
            db.add(Membership(
                organization_id=org_id, user_id=user.id, role="customer",
            ))

        # Water app role 'customer'.
        water_app = await db.scalar(
            select(AppRegistry).where(AppRegistry.code == "water")
        )
        if water_app is None:
            raise ValidationError("La app 'water' no está registrada en el sistema.")
        app_role = await db.scalar(
            select(AppUserRole).where(
                AppUserRole.organization_id == org_id,
                AppUserRole.user_id == user.id,
                AppUserRole.app_id == water_app.id,
            )
        )
        if app_role is None:
            db.add(AppUserRole(
                organization_id=org_id, user_id=user.id,
                app_id=water_app.id, role="customer",
            ))
        else:
            app_role.role = "customer"

        # Link subscriber.
        sub.user_id = user.id
        await db.flush()

        return InvitePortalResponse(
            user_id=user.id,
            email=user.email,
            name=user.name,
            created_new_user=created_new_user,
        )
