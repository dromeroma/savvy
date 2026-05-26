"""DDL setup para SavvyMemorial fase 3 — facturas, pagos, allocations.
Idempotente."""

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
    # ---------- memorial_invoices ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_invoices (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        consecutive INTEGER NOT NULL,
        code VARCHAR(20) NOT NULL,

        source_type VARCHAR(20) NOT NULL,
        contract_id UUID REFERENCES memorial_exequial_contracts(id) ON DELETE SET NULL,
        service_id UUID REFERENCES memorial_services(id) ON DELETE SET NULL,

        responsible_name VARCHAR(255) NOT NULL,
        responsible_document VARCHAR(50),
        responsible_email VARCHAR(255),
        responsible_phone VARCHAR(50),
        responsible_address VARCHAR(255),

        period_start DATE,
        period_end DATE,

        issue_date DATE NOT NULL,
        due_date DATE NOT NULL,

        subtotal NUMERIC(14,2) NOT NULL DEFAULT 0,
        late_interest NUMERIC(14,2) NOT NULL DEFAULT 0,
        surcharges NUMERIC(14,2) NOT NULL DEFAULT 0,
        discounts NUMERIC(14,2) NOT NULL DEFAULT 0,
        total NUMERIC(14,2) NOT NULL DEFAULT 0,
        paid_amount NUMERIC(14,2) NOT NULL DEFAULT 0,
        balance NUMERIC(14,2) NOT NULL DEFAULT 0,

        status VARCHAR(20) NOT NULL DEFAULT 'pending',

        description TEXT,
        notes TEXT,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,

        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        CONSTRAINT uq_memorial_invoices_org_consec UNIQUE (organization_id, consecutive),
        CONSTRAINT uq_memorial_invoices_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_invoices_source CHECK (
            source_type IN ('exequial_dues','service')
        ),
        CONSTRAINT chk_memorial_invoices_status CHECK (
            status IN ('pending','partial','paid','overdue','annulled')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_invoices_org ON memorial_invoices(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_invoices_contract ON memorial_invoices(contract_id) WHERE contract_id IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_memorial_invoices_service ON memorial_invoices(service_id) WHERE service_id IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_memorial_invoices_status ON memorial_invoices(status)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_invoices_due_date ON memorial_invoices(due_date)",

    # Garantizar que no se genere doble cuota para mismo contrato + periodo
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_memorial_invoices_contract_period
        ON memorial_invoices(contract_id, period_start)
        WHERE contract_id IS NOT NULL AND status != 'annulled'
    """,
    # Una factura no anulada por servicio
    """
    CREATE UNIQUE INDEX IF NOT EXISTS uq_memorial_invoices_service_one
        ON memorial_invoices(service_id)
        WHERE service_id IS NOT NULL AND status != 'annulled'
    """,

    # ---------- memorial_payments ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_payments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        consecutive INTEGER NOT NULL,
        code VARCHAR(20) NOT NULL,

        contract_id UUID REFERENCES memorial_exequial_contracts(id) ON DELETE SET NULL,
        service_id UUID REFERENCES memorial_services(id) ON DELETE SET NULL,

        payer_name VARCHAR(255) NOT NULL,
        payer_document VARCHAR(50),
        payer_email VARCHAR(255),
        payer_phone VARCHAR(50),

        payment_date DATE NOT NULL,
        amount NUMERIC(14,2) NOT NULL CHECK (amount > 0),
        method VARCHAR(30) NOT NULL DEFAULT 'cash',
        receipt_number VARCHAR(40),
        reference VARCHAR(100),
        notes TEXT,
        recorded_by UUID REFERENCES users(id) ON DELETE SET NULL,

        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        CONSTRAINT uq_memorial_payments_org_consec UNIQUE (organization_id, consecutive),
        CONSTRAINT uq_memorial_payments_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_payments_method CHECK (
            method IN ('cash','transfer','card','check','online')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_payments_org ON memorial_payments(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_payments_contract ON memorial_payments(contract_id) WHERE contract_id IS NOT NULL",
    "CREATE INDEX IF NOT EXISTS ix_memorial_payments_date ON memorial_payments(payment_date)",

    # ---------- memorial_payment_invoices (allocation) ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_payment_invoices (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        payment_id UUID NOT NULL REFERENCES memorial_payments(id) ON DELETE CASCADE,
        invoice_id UUID NOT NULL REFERENCES memorial_invoices(id) ON DELETE CASCADE,
        amount NUMERIC(14,2) NOT NULL CHECK (amount > 0),
        CONSTRAINT uq_memorial_pi UNIQUE (payment_id, invoice_id)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_pi_invoice ON memorial_payment_invoices(invoice_id)",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyMemorial · setup DDL fase 3 (invoices + payments + allocations)")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, start=1):
            label = stmt.strip().splitlines()[0][:80]
            print(f"  [{i:2d}/{len(DDL)}] {label}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — schema fase 3 listo.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
