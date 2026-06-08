"""DDL setup para SavvyFlow (sub-fase 3b) — automatizaciones no-code.

Tablas:
  - automation_workflows     (un flujo: trigger + metadatos)
  - automation_steps         (pasos del flujo: condiciones y acciones)
  - automation_runs          (historial de ejecuciones + log)
  - automation_notifications (bandeja de SavvyFlow: salida de la acción 'notify')

Idempotente.
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
    """
    CREATE TABLE IF NOT EXISTS automation_workflows (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        trigger_type VARCHAR(40) NOT NULL,
        trigger_config JSONB NOT NULL DEFAULT '{}'::jsonb,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        run_count INTEGER NOT NULL DEFAULT 0,
        last_run_at TIMESTAMPTZ,
        last_status VARCHAR(20),
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_flow_trigger CHECK (
            trigger_type IN ('manual','schedule_daily','pos_low_stock','memorial_overdue')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_flow_wf_org ON automation_workflows(organization_id, is_active)",
    """
    CREATE TABLE IF NOT EXISTS automation_steps (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        workflow_id UUID NOT NULL REFERENCES automation_workflows(id) ON DELETE CASCADE,
        sort_order INTEGER NOT NULL DEFAULT 0,
        kind VARCHAR(20) NOT NULL,
        type VARCHAR(40) NOT NULL,
        config JSONB NOT NULL DEFAULT '{}'::jsonb,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_flow_step_kind CHECK (kind IN ('condition','action'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_flow_steps_wf ON automation_steps(workflow_id, sort_order)",
    """
    CREATE TABLE IF NOT EXISTS automation_runs (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        workflow_id UUID NOT NULL REFERENCES automation_workflows(id) ON DELETE CASCADE,
        status VARCHAR(20) NOT NULL DEFAULT 'running',
        trigger_source VARCHAR(40),
        items_matched INTEGER NOT NULL DEFAULT 0,
        log JSONB NOT NULL DEFAULT '[]'::jsonb,
        error TEXT,
        started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        finished_at TIMESTAMPTZ,
        CONSTRAINT chk_flow_run_status CHECK (status IN ('running','succeeded','failed','skipped'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_flow_runs_wf ON automation_runs(workflow_id, started_at DESC)",
    """
    CREATE TABLE IF NOT EXISTS automation_notifications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        workflow_id UUID REFERENCES automation_workflows(id) ON DELETE SET NULL,
        run_id UUID REFERENCES automation_runs(id) ON DELETE SET NULL,
        level VARCHAR(20) NOT NULL DEFAULT 'info',
        title VARCHAR(200) NOT NULL,
        body TEXT,
        link VARCHAR(200),
        read_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_flow_notif_org ON automation_notifications(organization_id, created_at DESC)",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyFlow · setup DDL sub-fase 3b (automatizaciones no-code)")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, 1):
            print(f"  [{i:>2}/{len(DDL)}] {' '.join(stmt.split())[:84]}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — schema SavvyFlow listo.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
