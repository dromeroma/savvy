"""SavvyMemorial SQLAlchemy models.

Phase 1: servicios funerarios (núcleo del módulo). Tablas extra que no se
usan en fase 1 pero ya existen en la DB (memorial_notifications,
memorial_audit_log) tienen su modelo aquí para que se enganche con la
infra de notificaciones y auditoría desde el día 1.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


# ---------------------------------------------------------------- Service


class MemorialService(BaseMixin, OrgMixin, Base):
    """Servicio funerario — la entidad central de SavvyMemorial."""

    __tablename__ = "memorial_services"
    __table_args__ = (
        UniqueConstraint("organization_id", "consecutive", name="uq_memorial_services_org_consec"),
        UniqueConstraint("organization_id", "code", name="uq_memorial_services_org_code"),
        CheckConstraint(
            "status IN ('iniciado','en_proceso','pendiente','finalizado','cancelado')",
            name="chk_memorial_services_status",
        ),
        CheckConstraint(
            "service_type IN ("
            "'velacion','cremacion','entierro',"
            "'velacion_cremacion','velacion_entierro',"
            "'velacion_cremacion_entierro')",
            name="chk_memorial_services_type",
        ),
    )

    consecutive: Mapped[int] = mapped_column(nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)

    # Fallecido
    deceased_first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    deceased_last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    deceased_document_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    deceased_document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    deceased_birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    deceased_death_date: Mapped[date] = mapped_column(Date, nullable=False)
    deceased_death_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    deceased_death_cause: Mapped[str | None] = mapped_column(String(255), nullable=True)
    deceased_death_place: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Configuración
    service_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="iniciado", nullable=False)

    # Ejecución
    velation_start_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    velation_end_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    velation_location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    cremation_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cremation_location: Mapped[str | None] = mapped_column(String(255), nullable=True)

    burial_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    burial_cemetery: Mapped[str | None] = mapped_column(String(255), nullable=True)
    burial_section: Mapped[str | None] = mapped_column(String(100), nullable=True)

    mass_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    mass_church: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Pricing (la facturación entra en fase 3)
    estimated_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False,
    )
    final_total: Mapped[Decimal] = mapped_column(
        Numeric(14, 2), default=Decimal("0"), nullable=False,
    )

    exequial_contract_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    # Fase 4 — logística (FKs opcionales que reemplazan los campos texto)
    velation_room_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    cremation_oven_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    cemetery_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    church_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    family_members: Mapped[list[MemorialServiceFamily]] = relationship(
        "MemorialServiceFamily", back_populates="service",
        cascade="all, delete-orphan",
    )
    events: Mapped[list[MemorialServiceEvent]] = relationship(
        "MemorialServiceEvent", back_populates="service",
        cascade="all, delete-orphan",
    )


# ---------------------------------------------------------------- Family


class MemorialServiceFamily(BaseMixin, OrgMixin, Base):
    """Familiar responsable o de contacto en un servicio."""

    __tablename__ = "memorial_service_family"

    service_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("memorial_services.id", ondelete="CASCADE"), nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    relationship_: Mapped[str | None] = mapped_column("relationship", String(50), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    service: Mapped[MemorialService] = relationship(
        "MemorialService", back_populates="family_members",
    )


# ---------------------------------------------------------------- Events


class MemorialServiceEvent(Base):
    """Timeline de eventos por servicio: cambios de estado, notas,
    asignaciones, etc. Distinto del audit_log global — esto es lo que se
    pinta en el detalle del servicio."""

    __tablename__ = "memorial_service_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    service_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("memorial_services.id", ondelete="CASCADE"), nullable=False,
    )
    event_type: Mapped[str] = mapped_column(String(40), nullable=False)
    event_data: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    service: Mapped[MemorialService] = relationship(
        "MemorialService", back_populates="events",
    )


# ---------------------------------------------------------------- Notifications + Audit


class MemorialNotification(Base):
    """In-app notification para usuarios del módulo Memorial."""

    __tablename__ = "memorial_notifications"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    link: Mapped[str | None] = mapped_column(String(255), nullable=True)
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


# ---------------------------------------------------------------- Phase 2: Exequial plans


class MemorialExequialPlan(BaseMixin, OrgMixin, Base):
    """Catálogo de planes exequiales que vende la funeraria."""

    __tablename__ = "memorial_exequial_plans"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_memorial_plans_org_code"),
        CheckConstraint(
            "plan_type IN ('individual','familiar','empresarial')",
            name="chk_memorial_plans_type",
        ),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False)
    max_beneficiaries: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age_at_affiliation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max_age_for_coverage: Mapped[int | None] = mapped_column(Integer, nullable=True)
    waiting_period_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    monthly_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    quarterly_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    semiannual_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    annual_fee: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)

    coverage_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    coverage_items: Mapped[list | None] = mapped_column(JSONB, default=list)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    valid_from: Mapped[date] = mapped_column(Date, nullable=False)
    valid_to: Mapped[date | None] = mapped_column(Date, nullable=True)


class MemorialExequialContract(BaseMixin, OrgMixin, Base):
    """Contrato exequial firmado por un afiliado o empresa."""

    __tablename__ = "memorial_exequial_contracts"
    __table_args__ = (
        UniqueConstraint("organization_id", "consecutive", name="uq_memorial_contracts_org_consec"),
        UniqueConstraint("organization_id", "code", name="uq_memorial_contracts_org_code"),
        CheckConstraint(
            "status IN ('active','suspended','cancelled','expired')",
            name="chk_memorial_contracts_status",
        ),
        CheckConstraint(
            "affiliate_type IN ('individual','familiar','empresarial')",
            name="chk_memorial_contracts_affiliate",
        ),
        CheckConstraint(
            "payment_frequency IN ('monthly','quarterly','semiannual','annual')",
            name="chk_memorial_contracts_freq",
        ),
    )

    consecutive: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    plan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("memorial_exequial_plans.id", ondelete="RESTRICT"), nullable=False,
    )

    affiliate_type: Mapped[str] = mapped_column(String(20), nullable=False)

    titular_first_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    titular_last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    titular_business_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    titular_document_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    titular_document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    titular_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    titular_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    titular_mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    titular_address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    payment_frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    fee_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), default=Decimal("0"), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    next_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    suspended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )

    beneficiaries: Mapped[list[MemorialExequialBeneficiary]] = relationship(
        "MemorialExequialBeneficiary", back_populates="contract",
        cascade="all, delete-orphan",
    )
    plan: Mapped[MemorialExequialPlan] = relationship("MemorialExequialPlan")


class MemorialExequialBeneficiary(BaseMixin, OrgMixin, Base):
    """Persona cubierta dentro de un contrato exequial."""

    __tablename__ = "memorial_exequial_beneficiaries"

    contract_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("memorial_exequial_contracts.id", ondelete="CASCADE"), nullable=False,
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    birth_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    gender: Mapped[str | None] = mapped_column(String(10), nullable=True)
    relationship_: Mapped[str | None] = mapped_column("relationship", String(50), nullable=True)
    is_titular: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    joined_at: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    removed_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    removed_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)

    contract: Mapped[MemorialExequialContract] = relationship(
        "MemorialExequialContract", back_populates="beneficiaries",
    )


# ---------------------------------------------------------------- Phase 3: Invoices + Payments


class MemorialInvoice(BaseMixin, OrgMixin, Base):
    """Factura. Cubre tanto cuotas exequiales (source_type='exequial_dues')
    como cobro por servicio funerario (source_type='service')."""

    __tablename__ = "memorial_invoices"
    __table_args__ = (
        UniqueConstraint("organization_id", "consecutive", name="uq_memorial_invoices_org_consec"),
        UniqueConstraint("organization_id", "code", name="uq_memorial_invoices_org_code"),
        CheckConstraint(
            "source_type IN ('exequial_dues','service')",
            name="chk_memorial_invoices_source",
        ),
        CheckConstraint(
            "status IN ('pending','partial','paid','overdue','annulled')",
            name="chk_memorial_invoices_status",
        ),
    )

    consecutive: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    source_type: Mapped[str] = mapped_column(String(20), nullable=False)
    contract_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memorial_exequial_contracts.id", ondelete="SET NULL"), nullable=True,
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memorial_services.id", ondelete="SET NULL"), nullable=True,
    )

    responsible_name: Mapped[str] = mapped_column(String(255), nullable=False)
    responsible_document: Mapped[str | None] = mapped_column(String(50), nullable=True)
    responsible_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    responsible_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    responsible_address: Mapped[str | None] = mapped_column(String(255), nullable=True)

    period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    period_end: Mapped[date | None] = mapped_column(Date, nullable=True)

    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)

    subtotal: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    late_interest: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    surcharges: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    discounts: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    total: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    paid_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0"), nullable=False)

    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


class MemorialPayment(BaseMixin, OrgMixin, Base):
    """Pago realizado por un titular o familiar responsable."""

    __tablename__ = "memorial_payments"
    __table_args__ = (
        UniqueConstraint("organization_id", "consecutive", name="uq_memorial_payments_org_consec"),
        UniqueConstraint("organization_id", "code", name="uq_memorial_payments_org_code"),
        CheckConstraint(
            "method IN ('cash','transfer','card','check','online')",
            name="chk_memorial_payments_method",
        ),
    )

    consecutive: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    contract_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memorial_exequial_contracts.id", ondelete="SET NULL"), nullable=True,
    )
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memorial_services.id", ondelete="SET NULL"), nullable=True,
    )

    payer_name: Mapped[str] = mapped_column(String(255), nullable=False)
    payer_document: Mapped[str | None] = mapped_column(String(50), nullable=True)
    payer_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    payer_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)

    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), default="cash", nullable=False)
    receipt_number: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    recorded_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


class MemorialPaymentInvoice(Base):
    """Allocation: cuánto del pago se aplicó a cuál factura."""

    __tablename__ = "memorial_payment_invoices"
    __table_args__ = (
        UniqueConstraint("payment_id", "invoice_id", name="uq_memorial_pi"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    payment_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("memorial_payments.id", ondelete="CASCADE"), nullable=False,
    )
    invoice_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("memorial_invoices.id", ondelete="CASCADE"), nullable=False,
    )
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)


# ---------------------------------------------------------------- Phase 4: Logística


class MemorialVehicle(BaseMixin, OrgMixin, Base):
    """Vehículo (carroza fúnebre, transporte familiar, utilitario)."""

    __tablename__ = "memorial_vehicles"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_memorial_vehicles_org_code"),
        UniqueConstraint("organization_id", "plate", name="uq_memorial_vehicles_org_plate"),
        CheckConstraint(
            "type IN ('hearse','family','utility','other')",
            name="chk_memorial_vehicles_type",
        ),
        CheckConstraint(
            "status IN ('active','maintenance','inactive')",
            name="chk_memorial_vehicles_status",
        ),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    plate: Mapped[str] = mapped_column(String(20), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(60), nullable=True)
    model: Mapped[str | None] = mapped_column(String(60), nullable=True)
    year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    type: Mapped[str] = mapped_column(String(20), default="hearse", nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    color: Mapped[str | None] = mapped_column(String(40), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    default_driver_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memorial_drivers.id", ondelete="SET NULL"), nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MemorialDriver(BaseMixin, OrgMixin, Base):
    """Conductor (recurso físico de la funeraria, no necesariamente
    Usuario de Savvy)."""

    __tablename__ = "memorial_drivers"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_memorial_drivers_org_code"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(10), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    license_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    license_category: Mapped[str | None] = mapped_column(String(10), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    mobile: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MemorialRoom(BaseMixin, OrgMixin, Base):
    """Sala de velación."""

    __tablename__ = "memorial_rooms"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_memorial_rooms_org_code"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MemorialOven(BaseMixin, OrgMixin, Base):
    """Horno crematorio."""

    __tablename__ = "memorial_ovens"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_memorial_ovens_org_code"),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    brand: Mapped[str | None] = mapped_column(String(60), nullable=True)
    model: Mapped[str | None] = mapped_column(String(60), nullable=True)
    daily_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class MemorialLocation(BaseMixin, OrgMixin, Base):
    """Cementerios e iglesias unificados con columna kind."""

    __tablename__ = "memorial_locations"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_memorial_locations_org_code"),
        CheckConstraint(
            "kind IN ('cemetery','church','other')",
            name="chk_memorial_locations_kind",
        ),
    )

    code: Mapped[str] = mapped_column(String(40), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str | None] = mapped_column(String(255), nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    contact_name: Mapped[str | None] = mapped_column(String(150), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class MemorialTransfer(BaseMixin, OrgMixin, Base):
    """Traslado: movimiento de un vehículo con conductor para un servicio.
    Tipos: pickup (recoger el cuerpo), to_velation, to_cremation, to_burial,
    to_mass, family (transporte familiar), other."""

    __tablename__ = "memorial_transfers"
    __table_args__ = (
        UniqueConstraint("organization_id", "consecutive", name="uq_memorial_transfers_org_consec"),
        UniqueConstraint("organization_id", "code", name="uq_memorial_transfers_org_code"),
        CheckConstraint(
            "transfer_type IN ('pickup','to_velation','to_cremation','to_burial','to_mass','family','other')",
            name="chk_memorial_transfers_type",
        ),
        CheckConstraint(
            "status IN ('scheduled','in_progress','completed','cancelled')",
            name="chk_memorial_transfers_status",
        ),
    )

    consecutive: Mapped[int] = mapped_column(Integer, nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    service_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memorial_services.id", ondelete="CASCADE"), nullable=True,
    )
    transfer_type: Mapped[str] = mapped_column(String(30), nullable=False)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memorial_vehicles.id", ondelete="SET NULL"), nullable=True,
    )
    driver_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("memorial_drivers.id", ondelete="SET NULL"), nullable=True,
    )
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    origin: Mapped[str | None] = mapped_column(String(255), nullable=True)
    destination: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )


# ---------------------------------------------------------------- Audit (back to original)


class MemorialAuditLog(Base):
    """Audit row para acciones que modifican estado en SavvyMemorial."""

    __tablename__ = "memorial_audit_log"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    action: Mapped[str] = mapped_column(String(80), nullable=False)
    resource_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    details: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(60), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(255), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
