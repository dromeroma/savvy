"""SavvyWater SQLAlchemy models — all phase 1 tables in one file.

Subscribers + meters get CRUD endpoints this phase. The rest exist in the
DB and as ORM models so subsequent phases (lectura, facturacion, pagos)
can plug in without another DDL migration.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


# =====================================================================
# Subscribers (clientes del acueducto)
# =====================================================================


class WaterSubscriber(BaseMixin, OrgMixin, Base):
    """A subscriber (client) of the water utility."""

    __tablename__ = "water_subscribers"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_water_sub_org_code"),
        CheckConstraint(
            "status IN ('active','suspended','overdue','retired')",
            name="chk_water_sub_status",
        ),
        CheckConstraint(
            "subscriber_type IN ('residential','commercial','industrial','official')",
            name="chk_water_sub_type",
        ),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    document_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    neighborhood: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("geo_cities.id", ondelete="SET NULL"), nullable=True,
    )
    stratum: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    subscriber_type: Mapped[str] = mapped_column(
        String(20), default="residential", nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    latitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[Decimal | None] = mapped_column(Numeric(10, 7), nullable=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    registered_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    retired_at: Mapped[date | None] = mapped_column(Date, nullable=True)

    meters: Mapped[list[WaterMeter]] = relationship(
        "WaterMeter", back_populates="subscriber",
    )


# =====================================================================
# Meters
# =====================================================================


class WaterMeter(BaseMixin, OrgMixin, Base):
    """A physical water meter, optionally linked to a subscriber."""

    __tablename__ = "water_meters"
    __table_args__ = (
        UniqueConstraint("organization_id", "serial_number", name="uq_water_meter_org_serial"),
        CheckConstraint(
            "status IN ('active','replaced','damaged','inactive')",
            name="chk_water_meter_status",
        ),
    )

    subscriber_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("water_subscribers.id", ondelete="SET NULL"), nullable=True,
    )
    serial_number: Mapped[str] = mapped_column(String(60), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(60), nullable=True)
    model: Mapped[str | None] = mapped_column(String(60), nullable=True)
    diameter: Mapped[str | None] = mapped_column(String(20), nullable=True)
    install_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    initial_reading: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
    )
    last_reading: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0"), nullable=False,
    )
    last_reading_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    location_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    subscriber: Mapped[WaterSubscriber | None] = relationship(
        "WaterSubscriber", back_populates="meters",
    )


# =====================================================================
# Tariffs (model only — no CRUD in phase 1)
# =====================================================================


class WaterTariff(BaseMixin, OrgMixin, Base):
    __tablename__ = "water_tariffs"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_water_tariff_org_code"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    subscriber_type: Mapped[str] = mapped_column(
        String(20), default="residential", nullable=False,
    )
    stratum: Mapped[int | None] = mapped_column(SmallInteger, nullable=True)
    fixed_charge: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    price_per_cubic: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    basic_limit_cubic: Mapped[Decimal | None] = mapped_column(Numeric(8, 2), nullable=True)
    surplus_price_per_cubic: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    reconnection_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    suspension_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    late_interest_rate: Mapped[Decimal] = mapped_column(Numeric(5, 4), default=Decimal("0"), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)


# =====================================================================
# Routes & Route-Subscribers (model only — no CRUD in phase 1)
# =====================================================================


class WaterRoute(BaseMixin, OrgMixin, Base):
    __tablename__ = "water_routes"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_water_route_org_code"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    collector_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class WaterRouteSubscriber(BaseMixin, OrgMixin, Base):
    __tablename__ = "water_route_subscribers"
    __table_args__ = (
        UniqueConstraint("route_id", "subscriber_id", name="uq_water_rs"),
    )

    route_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_routes.id", ondelete="CASCADE"), nullable=False,
    )
    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_subscribers.id", ondelete="CASCADE"), nullable=False,
    )
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)


# =====================================================================
# Consumptions (model only — no CRUD in phase 1)
# =====================================================================


class WaterConsumption(BaseMixin, OrgMixin, Base):
    __tablename__ = "water_consumptions"
    __table_args__ = (
        UniqueConstraint("meter_id", "period_year", "period_month", name="uq_water_cons_meter_period"),
        CheckConstraint("period_month BETWEEN 1 AND 12", name="chk_water_cons_month"),
    )

    meter_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_meters.id", ondelete="CASCADE"), nullable=False,
    )
    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_subscribers.id", ondelete="CASCADE"), nullable=False,
    )
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    reading_date: Mapped[date] = mapped_column(Date, nullable=False)
    previous_reading: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    current_reading: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    consumption_cubic: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    is_estimated: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# =====================================================================
# Invoices (model only — no CRUD in phase 1)
# =====================================================================


class WaterInvoice(BaseMixin, OrgMixin, Base):
    __tablename__ = "water_invoices"
    __table_args__ = (
        UniqueConstraint("organization_id", "consecutive", name="uq_water_inv_org_consec"),
        CheckConstraint(
            "status IN ('pending','paid','partial','overdue','annulled')",
            name="chk_water_inv_status",
        ),
    )

    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_subscribers.id", ondelete="CASCADE"), nullable=False,
    )
    consumption_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("water_consumptions.id", ondelete="SET NULL"), nullable=True,
    )
    consecutive: Mapped[int] = mapped_column(Integer, nullable=False)
    period_year: Mapped[int] = mapped_column(Integer, nullable=False)
    period_month: Mapped[int] = mapped_column(SmallInteger, nullable=False)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    fixed_charge: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    consumption_cubic: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"), nullable=False)
    consumption_charge: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    late_interest: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    surcharges: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    discounts: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    reconnection_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    suspension_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


# =====================================================================
# Payments (model only — no CRUD in phase 1)
# =====================================================================


class WaterPayment(BaseMixin, OrgMixin, Base):
    __tablename__ = "water_payments"
    __table_args__ = (
        CheckConstraint(
            "method IN ('cash','transfer','card','check','online')",
            name="chk_water_pay_method",
        ),
    )

    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_subscribers.id", ondelete="CASCADE"), nullable=False,
    )
    receipt_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), default="cash", nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    collector_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    cash_account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("water_cash_accounts.id", ondelete="SET NULL"), nullable=True,
    )


class WaterPaymentInvoice(Base):
    """Allocation of a payment across one or more invoices."""

    __tablename__ = "water_payment_invoices"
    __table_args__ = (
        UniqueConstraint("payment_id", "invoice_id", name="uq_water_pi"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_payments.id", ondelete="CASCADE"), nullable=False,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_invoices.id", ondelete="CASCADE"), nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)


# =====================================================================
# Treasury (Phase 4)
# =====================================================================


class WaterCashAccount(BaseMixin, OrgMixin, Base):
    """A cash/bank account for the water utility treasury."""

    __tablename__ = "water_cash_accounts"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_water_cash_org_code"),
        CheckConstraint("type IN ('cash','bank','other')", name="chk_water_cash_type"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), default="cash", nullable=False)
    initial_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False,
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class WaterTreasuryMovement(BaseMixin, OrgMixin, Base):
    """Income or expense movement against a cash account. Payments from
    /water/payments auto-create an `income` movement with category='water_payment'
    and payment_id linked, so the cash account balance stays in sync."""

    __tablename__ = "water_treasury_movements"
    __table_args__ = (
        CheckConstraint("type IN ('income','expense')", name="chk_water_treas_type"),
        CheckConstraint("amount > 0", name="chk_water_treas_amount"),
    )

    cash_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_cash_accounts.id", ondelete="CASCADE"), nullable=False,
    )
    movement_date: Mapped[date] = mapped_column(Date, nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    payment_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("water_payments.id", ondelete="SET NULL"), nullable=True,
    )
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


class WaterCashClosing(Base):
    """A cash closing (arqueo): expected vs counted balance for a given day."""

    __tablename__ = "water_cash_closings"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    cash_account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_cash_accounts.id", ondelete="CASCADE"), nullable=False,
    )
    closing_date: Mapped[date] = mapped_column(Date, nullable=False)
    expected_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    counted_balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    difference: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    closed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


# =====================================================================
# PQRS (Phase 5) — Peticiones, Quejas, Reclamos, Sugerencias
# =====================================================================


class WaterPqrs(BaseMixin, OrgMixin, Base):
    __tablename__ = "water_pqrs"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_water_pqrs_org_code"),
        CheckConstraint(
            "type IN ('peticion','queja','reclamo','sugerencia')",
            name="chk_water_pqrs_type",
        ),
        CheckConstraint(
            "status IN ('open','in_progress','resolved','closed')",
            name="chk_water_pqrs_status",
        ),
    )

    subscriber_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("water_subscribers.id", ondelete="CASCADE"), nullable=False,
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    subject: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    response: Mapped[str | None] = mapped_column(Text, nullable=True)
    responded_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    responded_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
