"""Medición de uso de IA — el corazón del modelo de negocio.

Registra CADA llamada con sus 5 dimensiones (org · usuario · módulo · acción ·
prompt) + tokens + costo, y mantiene el acumulado por org para el control de cuota.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.config import get_settings
from src.modules.savvy_ai.client import LLMResult
from src.modules.savvy_ai.models import AiOrgSettings, AiUsage
from src.modules.savvy_ai.pricing import compute_cost


class QuotaExceededError(Exception):
    """La organización superó su cuota mensual de tokens o el límite de gasto diario."""


async def check_daily_budget(db: AsyncSession, org_id: uuid.UUID) -> None:
    """Kill-switch: bloquea si el gasto de IA de hoy supera el límite global o por org.

    Defiende contra loops/abuso antes de que la cuota mensual reaccione.
    """
    s = get_settings()
    gl = s.AI_DAILY_USD_LIMIT_GLOBAL
    ol = s.AI_DAILY_USD_LIMIT_ORG
    if gl <= 0 and ol <= 0:
        return
    row = (await db.execute(text("""
        SELECT
          coalesce(sum(cost_usd),0) AS total,
          coalesce(sum(cost_usd) FILTER (WHERE organization_id = :org),0) AS org_total
        FROM ai_usage WHERE created_at::date = now()::date
    """), {"org": org_id})).mappings().first()
    if gl > 0 and float(row["total"]) >= gl:
        raise QuotaExceededError(
            "Se alcanzó el límite global de gasto de IA por hoy. Intenta mañana."
        )
    if ol > 0 and float(row["org_total"]) >= ol:
        raise QuotaExceededError(
            "Esta organización alcanzó su límite de gasto de IA por hoy."
        )


@dataclass
class CallContext:
    organization_id: uuid.UUID
    user_id: uuid.UUID | None = None
    app_code: str | None = None
    feature: str | None = None
    action: str | None = None
    prompt_key: str | None = None
    prompt_version: str | None = None
    tier: str | None = None
    job_id: uuid.UUID | None = None


async def get_or_create_settings(db: AsyncSession, org_id: uuid.UUID) -> AiOrgSettings:
    row = (await db.execute(
        select(AiOrgSettings).where(AiOrgSettings.organization_id == org_id)
    )).scalar_one_or_none()
    if row is None:
        row = AiOrgSettings(organization_id=org_id)
        db.add(row)
        await db.flush()
    return row


async def check_quota(db: AsyncSession, org_id: uuid.UUID) -> AiOrgSettings:
    """Verifica que la org pueda usar IA. Lanza si está deshabilitada o sin cuota."""
    s = await get_or_create_settings(db, org_id)
    if not s.ai_enabled:
        raise QuotaExceededError("La IA está deshabilitada para esta organización.")
    _maybe_reset_period(s)
    if s.monthly_token_quota and s.tokens_used_this_period >= s.monthly_token_quota:
        raise QuotaExceededError(
            "Se alcanzó la cuota mensual de IA. Amplía el plan para continuar.",
        )
    # Kill-switch de gasto diario (global + per-org).
    await check_daily_budget(db, org_id)
    return s


def _maybe_reset_period(s: AiOrgSettings) -> None:
    today = datetime.now(UTC).date()
    if s.period_resets_at is None:
        s.period_resets_at = _first_of_next_month(today)
    elif today >= s.period_resets_at:
        s.tokens_used_this_period = 0
        s.cost_used_this_period = Decimal("0")
        s.period_resets_at = _first_of_next_month(today)


def _first_of_next_month(d: date) -> date:
    return date(d.year + (1 if d.month == 12 else 0), 1 if d.month == 12 else d.month + 1, 1)


async def record_usage(
    db: AsyncSession,
    ctx: CallContext,
    result: LLMResult,
    *,
    pricing_override: dict | None = None,
    success: bool = True,
) -> AiUsage:
    """Registra la llamada en ai_usage y actualiza el acumulado de la org.

    Esta es la función que hace que TODO quede medido.
    """
    cost = compute_cost(
        result.model,
        result.input_tokens,
        result.output_tokens,
        result.cached_tokens,
        pricing_override=pricing_override,
    )
    usage = AiUsage(
        organization_id=ctx.organization_id,
        user_id=ctx.user_id,
        job_id=ctx.job_id,
        app_code=ctx.app_code,
        feature=ctx.feature,
        action=ctx.action,
        prompt_key=ctx.prompt_key,
        prompt_version=ctx.prompt_version,
        model=result.model,
        tier=ctx.tier,
        input_tokens=result.input_tokens,
        output_tokens=result.output_tokens,
        cached_tokens=result.cached_tokens,
        cost_usd=cost,
        latency_ms=result.latency_ms,
        success=success,
    )
    db.add(usage)

    # Acumulado para cuota
    s = await get_or_create_settings(db, ctx.organization_id)
    _maybe_reset_period(s)
    s.tokens_used_this_period += result.input_tokens + result.output_tokens
    s.cost_used_this_period = Decimal(s.cost_used_this_period) + cost
    await db.flush()
    return usage
