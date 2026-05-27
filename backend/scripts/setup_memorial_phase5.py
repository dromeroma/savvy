"""DDL setup para SavvyMemorial fase 5 — inventario + RRHH. Idempotente."""

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
    # ---------- memorial_inventory_items ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_inventory_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(200) NOT NULL,
        category VARCHAR(40) NOT NULL,
        description TEXT,
        unit VARCHAR(20) NOT NULL DEFAULT 'unidad',
        current_stock NUMERIC(14,2) NOT NULL DEFAULT 0,
        min_stock NUMERIC(14,2) NOT NULL DEFAULT 0,
        max_stock NUMERIC(14,2),
        unit_cost NUMERIC(14,2) NOT NULL DEFAULT 0,
        sale_price NUMERIC(14,2) NOT NULL DEFAULT 0,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_inv_items_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_inv_category CHECK (
            category IN ('casket','urn','flowers','supplies','vehicle_supplies','other')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_inv_items_org_cat ON memorial_inventory_items(organization_id, category)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_inv_items_active ON memorial_inventory_items(organization_id, is_active)",

    # ---------- memorial_inventory_movements ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_inventory_movements (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        consecutive INTEGER NOT NULL,
        code VARCHAR(20) NOT NULL,
        item_id UUID NOT NULL REFERENCES memorial_inventory_items(id) ON DELETE RESTRICT,
        movement_type VARCHAR(20) NOT NULL,
        quantity NUMERIC(14,2) NOT NULL,
        unit_cost NUMERIC(14,2),
        reason VARCHAR(80),
        reference_doc VARCHAR(80),
        supplier VARCHAR(150),
        service_id UUID REFERENCES memorial_services(id) ON DELETE SET NULL,
        movement_date DATE NOT NULL DEFAULT CURRENT_DATE,
        notes TEXT,
        recorded_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_inv_mov_org_consec UNIQUE (organization_id, consecutive),
        CONSTRAINT uq_memorial_inv_mov_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_inv_mov_type CHECK (
            movement_type IN ('entry','exit','adjustment','transfer_out','transfer_in')
        ),
        CONSTRAINT chk_memorial_inv_mov_qty CHECK (quantity <> 0)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_inv_mov_item ON memorial_inventory_movements(item_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_inv_mov_org_date ON memorial_inventory_movements(organization_id, movement_date DESC)",

    # ---------- memorial_positions ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_positions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_positions_org_code UNIQUE (organization_id, code)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_positions_org ON memorial_positions(organization_id)",

    # ---------- memorial_employees ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_employees (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100),
        document_type VARCHAR(10),
        document_number VARCHAR(50),
        birth_date DATE,
        gender VARCHAR(10),
        email VARCHAR(255),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        address VARCHAR(255),
        position_id UUID REFERENCES memorial_positions(id) ON DELETE SET NULL,
        contract_type VARCHAR(30) NOT NULL DEFAULT 'indefinido',
        hire_date DATE NOT NULL,
        end_date DATE,
        base_salary NUMERIC(14,2) NOT NULL DEFAULT 0,
        default_shift VARCHAR(30),
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        driver_id UUID REFERENCES memorial_drivers(id) ON DELETE SET NULL,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_employees_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_memorial_employees_status CHECK (
            status IN ('active','on_leave','suspended','terminated')
        ),
        CONSTRAINT chk_memorial_employees_contract CHECK (
            contract_type IN ('indefinido','fijo','obra_labor','prestacion','aprendiz','otro')
        ),
        CONSTRAINT chk_memorial_employees_shift CHECK (
            default_shift IS NULL OR default_shift IN ('morning','afternoon','night','rotating','administrative')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_employees_org ON memorial_employees(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_employees_status ON memorial_employees(organization_id, status)",

    # ---------- memorial_attendance ----------
    """
    CREATE TABLE IF NOT EXISTS memorial_attendance (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES memorial_employees(id) ON DELETE CASCADE,
        work_date DATE NOT NULL,
        check_in_at TIMESTAMPTZ,
        check_out_at TIMESTAMPTZ,
        hours_worked NUMERIC(5,2),
        status VARCHAR(20) NOT NULL DEFAULT 'present',
        notes TEXT,
        recorded_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_memorial_att_emp_date UNIQUE (employee_id, work_date),
        CONSTRAINT chk_memorial_att_status CHECK (
            status IN ('present','absent','late','justified','vacation','sick_leave')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_memorial_att_org_date ON memorial_attendance(organization_id, work_date DESC)",
    "CREATE INDEX IF NOT EXISTS ix_memorial_att_employee ON memorial_attendance(employee_id, work_date DESC)",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyMemorial · setup DDL fase 5 (inventario + RRHH)")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, start=1):
            label = stmt.strip().splitlines()[0][:80]
            print(f"  [{i:2d}/{len(DDL)}] {label}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — schema fase 5 listo.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
