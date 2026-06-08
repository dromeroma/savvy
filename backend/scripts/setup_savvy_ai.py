"""DDL setup para el módulo SavvyAI (Fase 0 — cimiento).

Tablas:
  - ai_provider_config   (PLATAFORMA: API key cifrada + modelos + tarifas)
  - ai_org_settings      (por org: feature on/off + cuota mensual)
  - ai_jobs              (cola async de trabajos de IA)
  - ai_extractions       (resultado de SavvyScan, reutilizable)
  - ai_usage             (MEDICIÓN: org · usuario · módulo · acción · prompt · costo)
  - ai_audit_log         (trazabilidad: propuesto / confirmado / descartado)

Idempotente. Mide TODO desde el día uno — base del modelo de negocio.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import text  # noqa: E402

from src.core.database import async_session_factory, engine  # noqa: E402


DDL = [
    # -------- ai_provider_config (PLATAFORMA, no org) --------
    """
    CREATE TABLE IF NOT EXISTS ai_provider_config (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        provider VARCHAR(40) NOT NULL DEFAULT 'anthropic',
        api_key_encrypted TEXT,
        api_key_hint VARCHAR(20),
        is_enabled BOOLEAN NOT NULL DEFAULT FALSE,
        model_haiku VARCHAR(60) NOT NULL DEFAULT 'claude-haiku-4-5',
        model_sonnet VARCHAR(60) NOT NULL DEFAULT 'claude-sonnet-4-6',
        model_opus VARCHAR(60) NOT NULL DEFAULT 'claude-opus-4-8',
        default_tier VARCHAR(20) NOT NULL DEFAULT 'sonnet',
        pricing JSONB NOT NULL DEFAULT '{}'::jsonb,
        updated_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_ai_provider_tier CHECK (default_tier IN ('haiku','sonnet','opus'))
    )
    """,
    # -------- ai_org_settings --------
    """
    CREATE TABLE IF NOT EXISTS ai_org_settings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        ai_enabled BOOLEAN NOT NULL DEFAULT TRUE,
        monthly_token_quota BIGINT NOT NULL DEFAULT 0,
        tokens_used_this_period BIGINT NOT NULL DEFAULT 0,
        cost_used_this_period NUMERIC(12,4) NOT NULL DEFAULT 0,
        period_resets_at DATE,
        allowed_tiers JSONB NOT NULL DEFAULT '["haiku","sonnet","opus"]'::jsonb,
        features JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_ai_org_settings_org UNIQUE (organization_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_ai_org_settings_org ON ai_org_settings(organization_id)",
    # -------- ai_jobs --------
    """
    CREATE TABLE IF NOT EXISTS ai_jobs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        job_type VARCHAR(40) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'queued',
        source_kind VARCHAR(20),
        source_ref TEXT,
        app_code VARCHAR(40),
        action VARCHAR(80),
        model_used VARCHAR(60),
        input_summary TEXT,
        output JSONB,
        error TEXT,
        latency_ms INTEGER,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        completed_at TIMESTAMPTZ,
        CONSTRAINT chk_ai_jobs_status CHECK (
            status IN ('queued','running','succeeded','failed','cancelled')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_ai_jobs_org ON ai_jobs(organization_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_ai_jobs_status ON ai_jobs(organization_id, status)",
    # -------- ai_extractions --------
    """
    CREATE TABLE IF NOT EXISTS ai_extractions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        job_id UUID REFERENCES ai_jobs(id) ON DELETE SET NULL,
        document_type VARCHAR(40) NOT NULL,
        target_app VARCHAR(40),
        extracted_data JSONB NOT NULL DEFAULT '{}'::jsonb,
        confidence NUMERIC(5,2),
        field_confidence JSONB,
        status VARCHAR(20) NOT NULL DEFAULT 'pending_review',
        confirmed_entity_type VARCHAR(60),
        confirmed_entity_id UUID,
        confirmed_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_ai_extraction_status CHECK (
            status IN ('pending_review','confirmed','discarded')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_ai_extractions_org ON ai_extractions(organization_id, status)",
    # -------- ai_usage (MEDICIÓN COMPLETA) --------
    """
    CREATE TABLE IF NOT EXISTS ai_usage (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        job_id UUID REFERENCES ai_jobs(id) ON DELETE SET NULL,
        app_code VARCHAR(40),
        feature VARCHAR(60),
        action VARCHAR(80),
        prompt_key VARCHAR(80),
        prompt_version VARCHAR(20),
        model VARCHAR(60) NOT NULL,
        tier VARCHAR(20),
        input_tokens INTEGER NOT NULL DEFAULT 0,
        output_tokens INTEGER NOT NULL DEFAULT 0,
        cached_tokens INTEGER NOT NULL DEFAULT 0,
        cost_usd NUMERIC(12,6) NOT NULL DEFAULT 0,
        latency_ms INTEGER,
        success BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_ai_usage_org_date ON ai_usage(organization_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_ai_usage_org_app ON ai_usage(organization_id, app_code)",
    "CREATE INDEX IF NOT EXISTS ix_ai_usage_org_user ON ai_usage(organization_id, user_id)",
    "CREATE INDEX IF NOT EXISTS ix_ai_usage_org_action ON ai_usage(organization_id, action)",
    "CREATE INDEX IF NOT EXISTS ix_ai_usage_org_prompt ON ai_usage(organization_id, prompt_key)",
    # -------- ai_audit_log --------
    """
    CREATE TABLE IF NOT EXISTS ai_audit_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        job_id UUID REFERENCES ai_jobs(id) ON DELETE SET NULL,
        extraction_id UUID REFERENCES ai_extractions(id) ON DELETE SET NULL,
        action VARCHAR(30) NOT NULL,
        actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        app_code VARCHAR(40),
        summary TEXT,
        payload JSONB,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_ai_audit_action CHECK (
            action IN ('proposed','confirmed','edited','discarded','error')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_ai_audit_org ON ai_audit_log(organization_id, created_at DESC)",
    # -------- fila singleton de configuración de proveedor --------
    """
    INSERT INTO ai_provider_config (id, provider, is_enabled)
    SELECT gen_random_uuid(), 'anthropic', FALSE
    WHERE NOT EXISTS (SELECT 1 FROM ai_provider_config)
    """,
]


async def main() -> None:
    print("=" * 70)
    print("SavvyAI · setup DDL Fase 0 (cimiento + medición)")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, 1):
            preview = " ".join(stmt.split())[:88]
            print(f"  [{i:>2}/{len(DDL)}] {preview}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — schema SavvyAI Fase 0 listo.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
