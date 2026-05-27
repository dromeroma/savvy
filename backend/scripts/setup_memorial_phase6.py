"""DDL setup para SavvyMemorial fase 6 — CRM + portal cliente. Idempotente."""

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
    # ---------- memorial_leads ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_leads (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        consecutive INTEGER NOT NULL,
        code VARCHAR(20) NOT NULL,
        first_name VARCHAR(100),
        last_name VARCHAR(100),
        business_name VARCHAR(200),
        document_type VARCHAR(10),
        document_number VARCHAR(50),
        email VARCHAR(255),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        address VARCHAR(255),
        source VARCHAR(20) NOT NULL DEFAULT 'walk_in',
        interest VARCHAR(30) NOT NULL DEFAULT 'info',
        status VARCHAR(20) NOT NULL DEFAULT 'new',
        priority VARCHAR(10) NOT NULL DEFAULT 'medium',
        assigned_to UUID REFERENCES users(id) ON DELETE SET NULL,
        next_follow_up_at TIMESTAMPTZ,
        notes TEXT,
        converted_contract_id UUID REFERENCES memorial_exequial_contracts(id) ON DELETE SET NULL,
        converted_service_id UUID REFERENCES memorial_services(id) ON DELETE SET NULL,
        converted_at TIMESTAMPTZ,
        lost_reason VARCHAR(255),
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_leads_org_consec UNIQUE (organization_id, consecutive),
        CONSTRAINT uq_memorial_leads_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_leads_source CHECK (
            source IN ('referral','walk_in','web','social','whatsapp','phone','event','other')
        ),
        CONSTRAINT chk_memorial_leads_interest CHECK (
            interest IN ('exequial_plan','service_immediate','service_future','info','other')
        ),
        CONSTRAINT chk_memorial_leads_status CHECK (
            status IN ('new','contacted','qualified','proposal','won','lost')
        ),
        CONSTRAINT chk_memorial_leads_priority CHECK (
            priority IN ('low','medium','high','urgent')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_leads_org_status ON memorial_leads(organization_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_leads_assigned ON memorial_leads(assigned_to, status)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_leads_follow_up ON memorial_leads(organization_id, next_follow_up_at)",

    # ---------- memorial_lead_communications ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_lead_communications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        lead_id UUID NOT NULL REFERENCES memorial_leads(id) ON DELETE CASCADE,
        channel VARCHAR(20) NOT NULL,
        direction VARCHAR(10) NOT NULL DEFAULT 'outbound',
        subject VARCHAR(255),
        content TEXT,
        occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        outcome VARCHAR(40),
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_memorial_lead_comm_channel CHECK (
            channel IN ('call','email','whatsapp','visit','sms','meeting','note')
        ),
        CONSTRAINT chk_memorial_lead_comm_direction CHECK (
            direction IN ('inbound','outbound','internal')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_lead_comm_lead ON memorial_lead_communications(lead_id, occurred_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_lead_comm_org ON memorial_lead_communications(organization_id, occurred_at DESC)",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyMemorial · setup DDL fase 6 (CRM + portal)")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, start=1):
            label = stmt.strip().splitlines()[0][:80]
            print(f"  [{i:2d}/{len(DDL)}] {label}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — schema fase 6 listo.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
