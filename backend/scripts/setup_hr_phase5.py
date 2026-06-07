"""DDL setup para SavvyHR fase 5 — liquidación + settings.

Tablas:
  - hr_settings              (config HR por organización: plantillas PDF, firma)
  - hr_liquidations          (cabecera de la liquidación al terminar contrato)
  - hr_liquidation_items     (concepto + monto: devengados/deducciones)
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
    # ---------- hr_settings ----------
    """
    CREATE TABLE IF NOT EXISTS hr_settings (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        default_liquidation_template VARCHAR(20) NOT NULL DEFAULT 'formal',
        liquidation_notes_default TEXT,
        admin_name VARCHAR(150),
        admin_title VARCHAR(150),
        signature_url TEXT,
        logo_url TEXT,
        brand_color VARCHAR(20),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_settings_org UNIQUE (organization_id),
        CONSTRAINT chk_hr_settings_template CHECK (
            default_liquidation_template IN ('formal','moderna','compacta')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_settings_org ON hr_settings(organization_id)",
    # ---------- hr_liquidations ----------
    """
    CREATE TABLE IF NOT EXISTS hr_liquidations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
        contract_id UUID REFERENCES hr_contracts(id) ON DELETE SET NULL,
        liquidation_number VARCHAR(40) NOT NULL,
        termination_date DATE NOT NULL,
        termination_reason VARCHAR(30) NOT NULL,
        last_worked_date DATE NOT NULL,
        contract_start_date DATE NOT NULL,
        base_salary NUMERIC(14,2) NOT NULL DEFAULT 0,
        average_salary NUMERIC(14,2) NOT NULL DEFAULT 0,
        days_worked_total INTEGER NOT NULL DEFAULT 0,
        total_earnings NUMERIC(14,2) NOT NULL DEFAULT 0,
        total_deductions NUMERIC(14,2) NOT NULL DEFAULT 0,
        net_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
        currency VARCHAR(3) NOT NULL DEFAULT 'COP',
        status VARCHAR(20) NOT NULL DEFAULT 'draft',
        paid_at TIMESTAMPTZ,
        finalized_at TIMESTAMPTZ,
        notes TEXT,
        pdf_template VARCHAR(20),
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        finalized_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_liq_org_number UNIQUE (organization_id, liquidation_number),
        CONSTRAINT chk_hr_liq_reason CHECK (
            termination_reason IN (
                'voluntary','mutual','with_cause','without_cause',
                'end_of_contract','retirement','death','other'
            )
        ),
        CONSTRAINT chk_hr_liq_status CHECK (
            status IN ('draft','finalized','paid','cancelled')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_liq_org ON hr_liquidations(organization_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_hr_liq_employee ON hr_liquidations(employee_id, termination_date)",
    # ---------- hr_liquidation_items ----------
    """
    CREATE TABLE IF NOT EXISTS hr_liquidation_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        liquidation_id UUID NOT NULL REFERENCES hr_liquidations(id) ON DELETE CASCADE,
        concept_code VARCHAR(60) NOT NULL,
        concept_name VARCHAR(200) NOT NULL,
        kind VARCHAR(20) NOT NULL,
        quantity NUMERIC(10,2) NOT NULL DEFAULT 1,
        base_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
        rate NUMERIC(10,4),
        amount NUMERIC(14,2) NOT NULL DEFAULT 0,
        is_manual BOOLEAN NOT NULL DEFAULT FALSE,
        sort_order INTEGER NOT NULL DEFAULT 0,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_hr_liq_item_kind CHECK (kind IN ('earning','deduction'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_liq_items_liq ON hr_liquidation_items(liquidation_id, sort_order)",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyHR · setup DDL fase 5 (liquidación + settings)")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, 1):
            preview = " ".join(stmt.split())[:90]
            print(f"  [{i:>2}/{len(DDL)}] {preview}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — schema fase 5 listo.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
