"""DDL setup para SavvyHR fase 2 — turnos + asistencia + vacaciones + permisos.

Tablas:
  - hr_shifts                (turnos configurables)
  - hr_attendance            (marcaciones diarias con horas extras)
  - hr_vacation_balances     (saldo por año/empleado)
  - hr_vacation_requests     (solicitudes con flow approval)
  - hr_leaves                (incapacidades, licencias, permisos)
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
    # ---------- hr_shifts ----------
    """
    CREATE TABLE IF NOT EXISTS hr_shifts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        shift_type VARCHAR(20) NOT NULL DEFAULT 'morning',
        start_time TIME,
        end_time TIME,
        break_minutes INTEGER NOT NULL DEFAULT 0,
        days_of_week JSONB NOT NULL DEFAULT '[1,2,3,4,5]'::jsonb,
        weekly_hours NUMERIC(5,2),
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_shifts_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_hr_shifts_type CHECK (
            shift_type IN ('morning','afternoon','night','rotating','flexible','administrative')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_shifts_org ON hr_shifts(organization_id)",

    # ---------- hr_attendance ----------
    """
    CREATE TABLE IF NOT EXISTS hr_attendance (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
        shift_id UUID REFERENCES hr_shifts(id) ON DELETE SET NULL,
        work_date DATE NOT NULL,
        check_in_at TIMESTAMPTZ,
        check_out_at TIMESTAMPTZ,
        planned_hours NUMERIC(5,2),
        worked_hours NUMERIC(5,2),
        overtime_day_hours NUMERIC(5,2) NOT NULL DEFAULT 0,
        overtime_night_hours NUMERIC(5,2) NOT NULL DEFAULT 0,
        overtime_holiday_hours NUMERIC(5,2) NOT NULL DEFAULT 0,
        status VARCHAR(20) NOT NULL DEFAULT 'present',
        notes TEXT,
        recorded_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_att_emp_date UNIQUE (employee_id, work_date),
        CONSTRAINT chk_hr_att_status CHECK (
            status IN ('present','absent','late','early_leave','justified','vacation','sick_leave','permit','holiday')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_att_org_date ON hr_attendance(organization_id, work_date DESC)",
    "CREATE INDEX IF NOT EXISTS ix_hr_att_employee ON hr_attendance(employee_id, work_date DESC)",

    # ---------- hr_vacation_balances ----------
    """
    CREATE TABLE IF NOT EXISTS hr_vacation_balances (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
        period_year INTEGER NOT NULL,
        days_accrued NUMERIC(6,2) NOT NULL DEFAULT 0,
        days_taken NUMERIC(6,2) NOT NULL DEFAULT 0,
        days_pending NUMERIC(6,2) NOT NULL DEFAULT 0,
        days_compensated NUMERIC(6,2) NOT NULL DEFAULT 0,
        last_accrual_at TIMESTAMPTZ,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_vac_bal_emp_year UNIQUE (employee_id, period_year)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_vac_bal_org ON hr_vacation_balances(organization_id, period_year DESC)",

    # ---------- hr_vacation_requests ----------
    """
    CREATE TABLE IF NOT EXISTS hr_vacation_requests (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
        request_number VARCHAR(40) NOT NULL,
        request_type VARCHAR(20) NOT NULL DEFAULT 'paid',
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        days_count NUMERIC(6,2) NOT NULL,
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        request_reason TEXT,
        rejection_reason TEXT,
        compensation_amount NUMERIC(14,2),
        requested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        approved_at TIMESTAMPTZ,
        approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
        rejected_at TIMESTAMPTZ,
        rejected_by UUID REFERENCES users(id) ON DELETE SET NULL,
        cancelled_at TIMESTAMPTZ,
        notes TEXT,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_vac_req_org_number UNIQUE (organization_id, request_number),
        CONSTRAINT chk_hr_vac_req_type CHECK (
            request_type IN ('paid','compensation','unpaid')
        ),
        CONSTRAINT chk_hr_vac_req_status CHECK (
            status IN ('pending','approved','rejected','cancelled','completed')
        ),
        CONSTRAINT chk_hr_vac_req_dates CHECK (end_date >= start_date)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_vac_req_emp ON hr_vacation_requests(employee_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_hr_vac_req_org_status ON hr_vacation_requests(organization_id, status)",

    # ---------- hr_leaves ----------
    """
    CREATE TABLE IF NOT EXISTS hr_leaves (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
        leave_number VARCHAR(40) NOT NULL,
        leave_type VARCHAR(30) NOT NULL,
        subtype VARCHAR(40),
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        days_count NUMERIC(6,2) NOT NULL,
        is_paid BOOLEAN NOT NULL DEFAULT TRUE,
        paid_percentage NUMERIC(5,2),
        amount_paid NUMERIC(14,2),
        supporting_doc_url TEXT,
        supporting_doc_number VARCHAR(80),
        supporting_doc_issuer VARCHAR(150),
        diagnosis_code VARCHAR(20),
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        notes TEXT,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_leaves_org_number UNIQUE (organization_id, leave_number),
        CONSTRAINT chk_hr_leaves_type CHECK (
            leave_type IN ('medical','maternity','paternity','bereavement','unpaid','paid_other','study','remunerated_permit')
        ),
        CONSTRAINT chk_hr_leaves_status CHECK (
            status IN ('active','completed','cancelled')
        ),
        CONSTRAINT chk_hr_leaves_dates CHECK (end_date >= start_date)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_leaves_emp ON hr_leaves(employee_id, start_date DESC)",
    "CREATE INDEX IF NOT EXISTS ix_hr_leaves_org_type ON hr_leaves(organization_id, leave_type)",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyHR · setup DDL fase 2 (turnos + asistencia + vacaciones + permisos)")
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
