"""DDL setup para SavvyMemorial fase 2 — planes exequiales, contratos,
beneficiarios + FK desde servicios al contrato. Idempotente."""

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
    # ---------- memorial_exequial_plans ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_exequial_plans (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        plan_type VARCHAR(20) NOT NULL,  -- individual | familiar | empresarial
        max_beneficiaries INTEGER,
        max_age_at_affiliation INTEGER,
        max_age_for_coverage INTEGER,
        waiting_period_days INTEGER NOT NULL DEFAULT 0,

        monthly_fee NUMERIC(12,2) DEFAULT 0,
        quarterly_fee NUMERIC(12,2) DEFAULT 0,
        semiannual_fee NUMERIC(12,2) DEFAULT 0,
        annual_fee NUMERIC(12,2) DEFAULT 0,

        coverage_amount NUMERIC(14,2) DEFAULT 0,
        coverage_items JSONB DEFAULT '[]'::jsonb,

        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        valid_from DATE NOT NULL,
        valid_to DATE,

        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        CONSTRAINT uq_memorial_plans_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_plans_type CHECK (
            plan_type IN ('individual','familiar','empresarial')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_plans_org ON memorial_exequial_plans(organization_id)",

    # ---------- memorial_exequial_contracts ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_exequial_contracts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        consecutive INTEGER NOT NULL,
        code VARCHAR(20) NOT NULL,
        plan_id UUID NOT NULL REFERENCES memorial_exequial_plans(id) ON DELETE RESTRICT,

        affiliate_type VARCHAR(20) NOT NULL,  -- individual | familiar | empresarial

        -- Titular (persona o empresa)
        titular_first_name VARCHAR(100),
        titular_last_name VARCHAR(100),
        titular_business_name VARCHAR(255),
        titular_document_type VARCHAR(10),
        titular_document_number VARCHAR(50),
        titular_email VARCHAR(255),
        titular_phone VARCHAR(50),
        titular_mobile VARCHAR(50),
        titular_address VARCHAR(255),

        -- Pago
        payment_frequency VARCHAR(20) NOT NULL,  -- monthly | quarterly | semiannual | annual
        fee_amount NUMERIC(12,2) NOT NULL DEFAULT 0,
        start_date DATE NOT NULL,
        next_payment_date DATE,

        -- Estado
        status VARCHAR(20) NOT NULL DEFAULT 'active',  -- active | suspended | cancelled | expired
        suspended_at TIMESTAMPTZ,
        cancelled_at TIMESTAMPTZ,
        cancellation_reason TEXT,

        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        notes TEXT,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,

        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        CONSTRAINT uq_memorial_contracts_org_consec UNIQUE (organization_id, consecutive),
        CONSTRAINT uq_memorial_contracts_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_contracts_status CHECK (
            status IN ('active','suspended','cancelled','expired')
        ),
        CONSTRAINT chk_memorial_contracts_affiliate CHECK (
            affiliate_type IN ('individual','familiar','empresarial')
        ),
        CONSTRAINT chk_memorial_contracts_freq CHECK (
            payment_frequency IN ('monthly','quarterly','semiannual','annual')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_contracts_org ON memorial_exequial_contracts(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_contracts_status ON memorial_exequial_contracts(status)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_contracts_next_payment ON memorial_exequial_contracts(next_payment_date)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_contracts_titular_doc ON memorial_exequial_contracts(titular_document_number)",

    # ---------- memorial_exequial_beneficiaries ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_exequial_beneficiaries (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        contract_id UUID NOT NULL REFERENCES memorial_exequial_contracts(id) ON DELETE CASCADE,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100),
        document_type VARCHAR(10),
        document_number VARCHAR(50),
        birth_date DATE,
        gender VARCHAR(10),
        relationship VARCHAR(50),
        is_titular BOOLEAN NOT NULL DEFAULT FALSE,
        joined_at DATE NOT NULL DEFAULT CURRENT_DATE,
        removed_at DATE,
        removed_reason VARCHAR(255),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_beneficiaries_contract ON memorial_exequial_beneficiaries(contract_id)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_beneficiaries_doc ON memorial_exequial_beneficiaries(organization_id, document_number) WHERE document_number IS NOT NULL",

    # ---------- FK desde memorial_services al contrato ----------
    # Si el FK ya existe (alguien lo añadió antes), la sentencia falla silenciosa con IF NOT EXISTS
    # Postgres no soporta IF NOT EXISTS para constraints, hacemos un check con catalog primero
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint
            WHERE conname = 'fk_memorial_services_exequial_contract'
        ) THEN
            ALTER TABLE memorial_services
                ADD CONSTRAINT fk_memorial_services_exequial_contract
                FOREIGN KEY (exequial_contract_id)
                REFERENCES memorial_exequial_contracts(id)
                ON DELETE SET NULL;
        END IF;
    END $$
    """,
]


async def main() -> None:
    print("=" * 70)
    print("SavvyMemorial · setup DDL fase 2 (planes + contratos + beneficiarios)")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, start=1):
            label = stmt.strip().splitlines()[0][:80]
            print(f"  [{i:2d}/{len(DDL)}] {label}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — schema fase 2 listo.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
