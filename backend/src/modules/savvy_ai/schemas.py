"""SavvyAI Pydantic schemas — Fase 0."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


# ============================================================ Provider (super admin)


class ProviderConfigResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    provider: str
    is_enabled: bool
    has_api_key: bool
    api_key_hint: str | None
    model_haiku: str
    model_sonnet: str
    model_opus: str
    default_tier: str
    pricing: dict[str, Any]
    updated_at: datetime


class ProviderConfigUpdate(BaseModel):
    api_key: str | None = Field(None, description="Si se envía, reemplaza la actual (se cifra)")
    is_enabled: bool | None = None
    model_haiku: str | None = None
    model_sonnet: str | None = None
    model_opus: str | None = None
    default_tier: Literal["haiku", "sonnet", "opus"] | None = None
    pricing: dict[str, Any] | None = None


class ProviderTestResult(BaseModel):
    ok: bool
    message: str
    model: str | None = None
    latency_ms: int | None = None


# ============================================================ Org settings


class AiOrgSettingsResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    organization_id: uuid.UUID
    ai_enabled: bool
    monthly_token_quota: int
    tokens_used_this_period: int
    cost_used_this_period: Decimal
    period_resets_at: Any | None
    allowed_tiers: list[str]
    features: dict[str, Any]


class AiOrgSettingsUpdate(BaseModel):
    ai_enabled: bool | None = None
    monthly_token_quota: int | None = None
    allowed_tiers: list[str] | None = None
    features: dict[str, Any] | None = None


# ============================================================ Jobs / extractions


class JobResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    job_type: str
    status: str
    app_code: str | None
    action: str | None
    model_used: str | None
    output: dict[str, Any] | None
    error: str | None
    latency_ms: int | None
    created_at: datetime
    completed_at: datetime | None


class ExtractionField(BaseModel):
    key: str
    label: str
    value: Any
    confidence: float | None = None
    editable: bool = True


class ConfirmableAction(BaseModel):
    """Contrato que el frontend renderiza como tarjeta [Confirmar][Editar][Descartar]."""
    extraction_id: uuid.UUID
    title: str
    target_app: str | None
    document_type: str
    summary: str
    confidence: float | None
    fields: list[ExtractionField]
    line_items: list[dict[str, Any]] = []
    status: str
    actions: list[str] = ["confirm", "edit", "discard"]
    # Resumen de lo aplicado a la app destino al confirmar (Fase 1+)
    result_summary: str | None = None
    result: dict[str, Any] | None = None


class ExtractionConfirm(BaseModel):
    """Confirma una extracción, opcionalmente con datos editados por el usuario."""
    edited_data: dict[str, Any] | None = None
    note: str | None = None


# ============================================================ Usage / analytics


class UsageSummary(BaseModel):
    total_cost_usd: Decimal
    total_tokens: int
    total_calls: int
    quota: int
    tokens_used_this_period: int


class UsageBreakdownRow(BaseModel):
    key: str
    label: str
    calls: int
    tokens: int
    cost_usd: Decimal


class OrgUsageReport(BaseModel):
    organization_id: uuid.UUID
    summary: UsageSummary
    by_app: list[UsageBreakdownRow]
    by_action: list[UsageBreakdownRow]
    by_user: list[UsageBreakdownRow]
    by_prompt: list[UsageBreakdownRow]


class PlatformUsageRow(BaseModel):
    organization_id: uuid.UUID
    organization_name: str
    calls: int
    tokens: int
    cost_usd: Decimal


class PlatformUsageReport(BaseModel):
    total_cost_usd: Decimal
    total_tokens: int
    total_calls: int
    active_orgs: int
    by_organization: list[PlatformUsageRow]
    by_model: list[UsageBreakdownRow]
    by_app: list[UsageBreakdownRow]
