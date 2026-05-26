"""DDL setup for SavvyMemorial — applies all tables + registry entries
for phase 1 (servicios funerarios). Idempotent: re-running is safe.

Run:
    cd backend
    .venv/Scripts/python.exe scripts/setup_memorial_module.py
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
    # ---------- 1. app_registry ----------
    """
    INSERT INTO app_registry (id, code, name, description, icon, color, is_active)
    VALUES (gen_random_uuid(), 'memorial',
            'SavvyMemorial',
            'Gestión funeraria integral: servicios, planes exequiales, cartera, logística y portal del afiliado.',
            'flower', '#6B7280', TRUE)
    ON CONFLICT (code) DO UPDATE
      SET name = EXCLUDED.name,
          description = EXCLUDED.description,
          icon = EXCLUDED.icon,
          color = EXCLUDED.color,
          is_active = TRUE
    """,

    # ---------- 2. business_type_catalog ----------
    """
    INSERT INTO business_type_catalog (code, name, description, default_app_code, icon, color, sort_order, is_active)
    VALUES ('funeraria', 'Funeraria',
            'Gestión funeraria integral con planes exequiales',
            'memorial', 'flower', '#6B7280', 100, TRUE)
    ON CONFLICT (code) DO UPDATE
      SET name = EXCLUDED.name,
          description = EXCLUDED.description,
          default_app_code = EXCLUDED.default_app_code,
          icon = EXCLUDED.icon,
          color = EXCLUDED.color,
          is_active = TRUE
    """,

    # ---------- 3. memorial_services ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_services (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        consecutive INTEGER NOT NULL,
        code VARCHAR(20) NOT NULL,

        deceased_first_name VARCHAR(100) NOT NULL,
        deceased_last_name VARCHAR(100),
        deceased_document_type VARCHAR(10),
        deceased_document_number VARCHAR(50),
        deceased_birth_date DATE,
        deceased_death_date DATE NOT NULL,
        deceased_death_time TIME,
        deceased_death_cause VARCHAR(255),
        deceased_death_place VARCHAR(255),

        service_type VARCHAR(40) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'iniciado',

        velation_start_at TIMESTAMPTZ,
        velation_end_at TIMESTAMPTZ,
        velation_location VARCHAR(255),

        cremation_at TIMESTAMPTZ,
        cremation_location VARCHAR(255),

        burial_at TIMESTAMPTZ,
        burial_cemetery VARCHAR(255),
        burial_section VARCHAR(100),

        mass_at TIMESTAMPTZ,
        mass_church VARCHAR(255),

        estimated_total NUMERIC(14, 2) DEFAULT 0,
        final_total NUMERIC(14, 2) DEFAULT 0,

        exequial_contract_id UUID,  -- FK added in phase 2
        notes TEXT,
        closed_at TIMESTAMPTZ,
        closed_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,

        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

        CONSTRAINT uq_memorial_services_org_consec UNIQUE (organization_id, consecutive),
        CONSTRAINT uq_memorial_services_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_services_status CHECK (
            status IN ('iniciado','en_proceso','pendiente','finalizado','cancelado')
        ),
        CONSTRAINT chk_memorial_services_type CHECK (
            service_type IN (
                'velacion','cremacion','entierro',
                'velacion_cremacion','velacion_entierro',
                'velacion_cremacion_entierro'
            )
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_services_org ON memorial_services(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_services_status ON memorial_services(status)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_services_death_date ON memorial_services(deceased_death_date)",

    # ---------- 4. memorial_service_family ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_service_family (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        service_id UUID NOT NULL REFERENCES memorial_services(id) ON DELETE CASCADE,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100),
        document_type VARCHAR(10),
        document_number VARCHAR(50),
        relationship VARCHAR(50),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        email VARCHAR(255),
        address VARCHAR(255),
        is_primary BOOLEAN NOT NULL DEFAULT FALSE,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_service_family_service ON memorial_service_family(service_id)",

    # ---------- 5. memorial_service_events (timeline) ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_service_events (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        service_id UUID NOT NULL REFERENCES memorial_services(id) ON DELETE CASCADE,
        event_type VARCHAR(40) NOT NULL,
        event_data JSONB,
        body TEXT,
        actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_service_events_service ON memorial_service_events(service_id, created_at DESC)",

    # ---------- 6. memorial_notifications (parallel to water_notifications) ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_notifications (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        type VARCHAR(40) NOT NULL,
        title VARCHAR(255) NOT NULL,
        body TEXT,
        link VARCHAR(255),
        read_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_notifications_user ON memorial_notifications(user_id, read_at)",

    # ---------- 7. memorial_audit_log ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_audit_log (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        actor_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        action VARCHAR(80) NOT NULL,
        resource_type VARCHAR(60),
        resource_id UUID,
        details JSONB,
        ip_address VARCHAR(60),
        user_agent VARCHAR(255),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_audit_org_created ON memorial_audit_log(organization_id, created_at DESC)",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyMemorial · setup DDL")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, start=1):
            label = stmt.strip().splitlines()[0][:80]
            print(f"  [{i:2d}/{len(DDL)}] {label}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — schema + app registry ready.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
