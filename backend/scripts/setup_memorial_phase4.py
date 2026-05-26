"""DDL setup para SavvyMemorial fase 4 — logística operativa.
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
    # ---------- memorial_vehicles ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_vehicles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        plate VARCHAR(20) NOT NULL,
        brand VARCHAR(60),
        model VARCHAR(60),
        year INTEGER,
        type VARCHAR(20) NOT NULL DEFAULT 'hearse',
        capacity INTEGER,
        color VARCHAR(40),
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        default_driver_id UUID,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_vehicles_org_code UNIQUE (organization_id, code),
        CONSTRAINT uq_memorial_vehicles_org_plate UNIQUE (organization_id, plate),
        CONSTRAINT chk_memorial_vehicles_type CHECK (
            type IN ('hearse','family','utility','other')
        ),
        CONSTRAINT chk_memorial_vehicles_status CHECK (
            status IN ('active','maintenance','inactive')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_vehicles_org ON memorial_vehicles(organization_id)",

    # ---------- memorial_drivers ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_drivers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100),
        document_type VARCHAR(10),
        document_number VARCHAR(50),
        license_number VARCHAR(50),
        license_category VARCHAR(10),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        email VARCHAR(255),
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_drivers_org_code UNIQUE (organization_id, code)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_drivers_org ON memorial_drivers(organization_id)",

    # FK desde vehicles al driver (después de crear drivers)
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'fk_memorial_vehicles_default_driver'
        ) THEN
            ALTER TABLE memorial_vehicles
                ADD CONSTRAINT fk_memorial_vehicles_default_driver
                FOREIGN KEY (default_driver_id) REFERENCES memorial_drivers(id) ON DELETE SET NULL;
        END IF;
    END $$
    """,

    # ---------- memorial_rooms (salas de velación) ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_rooms (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(100) NOT NULL,
        capacity INTEGER,
        location VARCHAR(255),
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_rooms_org_code UNIQUE (organization_id, code)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_rooms_org ON memorial_rooms(organization_id)",

    # ---------- memorial_ovens (hornos crematorios) ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_ovens (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(100) NOT NULL,
        brand VARCHAR(60),
        model VARCHAR(60),
        daily_capacity INTEGER,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_ovens_org_code UNIQUE (organization_id, code)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_ovens_org ON memorial_ovens(organization_id)",

    # ---------- memorial_locations (cementerios + iglesias) ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_locations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(255) NOT NULL,
        kind VARCHAR(20) NOT NULL,
        address VARCHAR(255),
        city VARCHAR(100),
        contact_name VARCHAR(150),
        contact_phone VARCHAR(50),
        contact_email VARCHAR(255),
        notes TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_locations_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_locations_kind CHECK (kind IN ('cemetery','church','other'))
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_locations_org_kind ON memorial_locations(organization_id, kind)",

    # ---------- memorial_transfers (traslados) ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_transfers (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(20) NOT NULL,
        consecutive INTEGER NOT NULL,
        service_id UUID REFERENCES memorial_services(id) ON DELETE CASCADE,
        transfer_type VARCHAR(30) NOT NULL,
        vehicle_id UUID REFERENCES memorial_vehicles(id) ON DELETE SET NULL,
        driver_id UUID REFERENCES memorial_drivers(id) ON DELETE SET NULL,
        scheduled_at TIMESTAMPTZ NOT NULL,
        started_at TIMESTAMPTZ,
        completed_at TIMESTAMPTZ,
        origin VARCHAR(255),
        destination VARCHAR(255),
        status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
        notes TEXT,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_transfers_org_consec UNIQUE (organization_id, consecutive),
        CONSTRAINT uq_memorial_transfers_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_transfers_type CHECK (
            transfer_type IN ('pickup','to_velation','to_cremation','to_burial','to_mass','family','other')
        ),
        CONSTRAINT chk_memorial_transfers_status CHECK (
            status IN ('scheduled','in_progress','completed','cancelled')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_transfers_org ON memorial_transfers(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_transfers_service ON memorial_transfers(service_id)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_transfers_scheduled ON memorial_transfers(scheduled_at)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_transfers_status ON memorial_transfers(status)",

    # ---------- FKs en memorial_services ----------
    """
    ALTER TABLE memorial_services
        ADD COLUMN IF NOT EXISTS velation_room_id UUID,
        ADD COLUMN IF NOT EXISTS cremation_oven_id UUID,
        ADD COLUMN IF NOT EXISTS cemetery_id UUID,
        ADD COLUMN IF NOT EXISTS church_id UUID
    """,
    """
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_memorial_services_velation_room') THEN
            ALTER TABLE memorial_services ADD CONSTRAINT fk_memorial_services_velation_room
                FOREIGN KEY (velation_room_id) REFERENCES memorial_rooms(id) ON DELETE SET NULL;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_memorial_services_cremation_oven') THEN
            ALTER TABLE memorial_services ADD CONSTRAINT fk_memorial_services_cremation_oven
                FOREIGN KEY (cremation_oven_id) REFERENCES memorial_ovens(id) ON DELETE SET NULL;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_memorial_services_cemetery') THEN
            ALTER TABLE memorial_services ADD CONSTRAINT fk_memorial_services_cemetery
                FOREIGN KEY (cemetery_id) REFERENCES memorial_locations(id) ON DELETE SET NULL;
        END IF;
        IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_memorial_services_church') THEN
            ALTER TABLE memorial_services ADD CONSTRAINT fk_memorial_services_church
                FOREIGN KEY (church_id) REFERENCES memorial_locations(id) ON DELETE SET NULL;
        END IF;
    END $$
    """,
]


async def main() -> None:
    print("=" * 70)
    print("SavvyMemorial · setup DDL fase 4 (logística)")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, start=1):
            label = stmt.strip().splitlines()[0][:80]
            print(f"  [{i:2d}/{len(DDL)}] {label}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — schema fase 4 listo.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
