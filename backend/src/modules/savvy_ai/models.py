"""SavvyAI ORM models — Fase 0 (cimiento + medición)."""

from __future__ import annotations

import uuid
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


# ============================================================ Plataforma


class AiProviderConfig(Base):
    """Config global del proveedor de IA (PLATAFORMA). Fila singleton.

    La API key se guarda cifrada (Fernet). Se administra desde el panel
    del super admin — nunca desde una organización.
    """

    __tablename__ = "ai_provider_config"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    provider: Mapped[str] = mapped_column(String(40), default="anthropic", nullable=False)
    api_key_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    api_key_hint: Mapped[str | None] = mapped_column(String(20), nullable=True)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    model_haiku: Mapped[str] = mapped_column(String(60), default="claude-haiku-4-5", nullable=False)
    model_sonnet: Mapped[str] = mapped_column(String(60), default="claude-sonnet-4-6", nullable=False)
    model_opus: Mapped[str] = mapped_column(String(60), default="claude-opus-4-8", nullable=False)
    default_tier: Mapped[str] = mapped_column(String(20), default="sonnet", nullable=False)
    pricing: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    # WhatsApp Cloud API (Fase 4)
    whatsapp_enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    whatsapp_token_encrypted: Mapped[str | None] = mapped_column(Text, nullable=True)
    whatsapp_token_hint: Mapped[str | None] = mapped_column(String(20), nullable=True)
    whatsapp_phone_id: Mapped[str | None] = mapped_column(String(60), nullable=True)
    updated_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


# ============================================================ Por organización


class AiOrgSettings(Base):
    """Config de IA por organización: feature on/off + cuota mensual."""

    __tablename__ = "ai_org_settings"
    __table_args__ = (
        UniqueConstraint("organization_id", name="uq_ai_org_settings_org"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
    )
    ai_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    monthly_token_quota: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    tokens_used_this_period: Mapped[int] = mapped_column(BigInteger, default=0, nullable=False)
    cost_used_this_period: Mapped[Decimal] = mapped_column(
        Numeric(12, 4), default=Decimal("0"), nullable=False,
    )
    period_resets_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    allowed_tiers: Mapped[list] = mapped_column(
        JSONB, default=lambda: ["haiku", "sonnet", "opus"], nullable=False,
    )
    features: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


class AiJob(Base):
    """Trabajo de IA (cola async)."""

    __tablename__ = "ai_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('queued','running','succeeded','failed','cancelled')",
            name="chk_ai_jobs_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
    )
    job_type: Mapped[str] = mapped_column(String(40), nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="queued", nullable=False)
    source_kind: Mapped[str | None] = mapped_column(String(20), nullable=True)
    source_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    app_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    action: Mapped[str | None] = mapped_column(String(80), nullable=True)
    model_used: Mapped[str | None] = mapped_column(String(60), nullable=True)
    input_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    output: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AiExtraction(Base):
    """Resultado de SavvyScan: documento → datos estructurados reutilizables."""

    __tablename__ = "ai_extractions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending_review','confirmed','discarded')",
            name="chk_ai_extraction_status",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_jobs.id", ondelete="SET NULL"), nullable=True,
    )
    document_type: Mapped[str] = mapped_column(String(40), nullable=False)
    target_app: Mapped[str | None] = mapped_column(String(40), nullable=True)
    extracted_data: Mapped[dict] = mapped_column(JSONB, default=dict, nullable=False)
    confidence: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True)
    field_confidence: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending_review", nullable=False)
    confirmed_entity_type: Mapped[str | None] = mapped_column(String(60), nullable=True)
    confirmed_entity_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


class AiUsage(Base):
    """MEDICIÓN COMPLETA de cada llamada al LLM.

    Captura las 5 dimensiones del modelo de negocio:
    org · usuario · módulo (app_code) · acción · prompt · costo.
    """

    __tablename__ = "ai_usage"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_jobs.id", ondelete="SET NULL"), nullable=True,
    )
    app_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    feature: Mapped[str | None] = mapped_column(String(60), nullable=True)
    action: Mapped[str | None] = mapped_column(String(80), nullable=True)
    prompt_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    model: Mapped[str] = mapped_column(String(60), nullable=False)
    tier: Mapped[str | None] = mapped_column(String(20), nullable=True)
    input_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    output_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cached_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(12, 6), default=Decimal("0"), nullable=False)
    latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    success: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


class AiAuditLog(Base):
    """Trazabilidad de toda acción de IA: propuesto/confirmado/editado/descartado."""

    __tablename__ = "ai_audit_log"
    __table_args__ = (
        CheckConstraint(
            "action IN ('proposed','confirmed','edited','discarded','error')",
            name="chk_ai_audit_action",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False,
    )
    job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_jobs.id", ondelete="SET NULL"), nullable=True,
    )
    extraction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("ai_extractions.id", ondelete="SET NULL"), nullable=True,
    )
    action: Mapped[str] = mapped_column(String(30), nullable=False)
    actor_user_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="SET NULL"), nullable=True,
    )
    app_code: Mapped[str | None] = mapped_column(String(40), nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    payload: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
