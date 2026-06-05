"""DDL setup para SavvyHR fase 3 — nómina completa.

Tablas:
  - hr_payroll_concepts      (catálogo configurable de conceptos)
  - hr_payroll_periods       (períodos: mensual/quincenal/semanal)
  - hr_payrolls              (liquidación por empleado por período)
  - hr_payroll_items         (líneas detalle: concepto × monto)
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
    # ---------- hr_payroll_concepts ----------
    """
    CREATE TABLE IF NOT EXISTS hr_payroll_concepts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        concept_type VARCHAR(30) NOT NULL,
        category VARCHAR(40) NOT NULL,
        calculation_method VARCHAR(20) NOT NULL DEFAULT 'fixed',
        formula TEXT,
        percentage_value NUMERIC(8,4),
        fixed_value NUMERIC(14,2),
        base_concept_code VARCHAR(40),
        country_code VARCHAR(3),
        is_taxable BOOLEAN NOT NULL DEFAULT TRUE,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        sort_order INTEGER NOT NULL DEFAULT 100,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_concepts_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_hr_concept_type CHECK (
            concept_type IN ('earning','deduction','benefit','employer_contribution','informative')
        ),
        CONSTRAINT chk_hr_concept_method CHECK (
            calculation_method IN ('fixed','percentage','formula','quantity_rate')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_concepts_org ON hr_payroll_concepts(organization_id, sort_order)",

    # ---------- hr_payroll_periods ----------
    """
    CREATE TABLE IF NOT EXISTS hr_payroll_periods (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(150) NOT NULL,
        period_type VARCHAR(20) NOT NULL DEFAULT 'monthly',
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        payment_date DATE,
        status VARCHAR(20) NOT NULL DEFAULT 'draft',
        total_gross NUMERIC(15,2) NOT NULL DEFAULT 0,
        total_deductions NUMERIC(15,2) NOT NULL DEFAULT 0,
        total_net NUMERIC(15,2) NOT NULL DEFAULT 0,
        employee_count INTEGER NOT NULL DEFAULT 0,
        calculated_at TIMESTAMPTZ,
        approved_at TIMESTAMPTZ,
        approved_by UUID REFERENCES users(id) ON DELETE SET NULL,
        paid_at TIMESTAMPTZ,
        paid_by UUID REFERENCES users(id) ON DELETE SET NULL,
        closed_at TIMESTAMPTZ,
        notes TEXT,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_periods_org_code UNIQUE (organization_id, code),
        CONSTRAINT chk_hr_period_type CHECK (
            period_type IN ('monthly','biweekly','weekly')
        ),
        CONSTRAINT chk_hr_period_status CHECK (
            status IN ('draft','calculating','calculated','approved','paid','closed','cancelled')
        ),
        CONSTRAINT chk_hr_period_dates CHECK (end_date >= start_date)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_periods_org ON hr_payroll_periods(organization_id, start_date DESC)",

    # ---------- hr_payrolls ----------
    """
    CREATE TABLE IF NOT EXISTS hr_payrolls (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        period_id UUID NOT NULL REFERENCES hr_payroll_periods(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
        contract_id UUID REFERENCES hr_contracts(id) ON DELETE SET NULL,
        employee_code VARCHAR(40) NOT NULL,
        employee_name VARCHAR(255) NOT NULL,
        department_name VARCHAR(150),
        position_name VARCHAR(150),
        base_salary NUMERIC(14,2) NOT NULL DEFAULT 0,
        worked_days NUMERIC(6,2) NOT NULL DEFAULT 30,
        absence_days NUMERIC(6,2) NOT NULL DEFAULT 0,
        total_earnings NUMERIC(15,2) NOT NULL DEFAULT 0,
        total_deductions NUMERIC(15,2) NOT NULL DEFAULT 0,
        total_benefits NUMERIC(15,2) NOT NULL DEFAULT 0,
        total_employer_contrib NUMERIC(15,2) NOT NULL DEFAULT 0,
        net_amount NUMERIC(15,2) NOT NULL DEFAULT 0,
        status VARCHAR(20) NOT NULL DEFAULT 'calculated',
        paid_at TIMESTAMPTZ,
        payment_reference VARCHAR(100),
        finance_transaction_id UUID,
        pay_transaction_id UUID,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_payroll_period_emp UNIQUE (period_id, employee_id),
        CONSTRAINT chk_hr_payroll_status CHECK (
            status IN ('pending','calculated','approved','paid','cancelled')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_payrolls_period ON hr_payrolls(period_id)",
    "CREATE INDEX IF NOT EXISTS ix_hr_payrolls_emp ON hr_payrolls(employee_id, status)",

    # ---------- hr_payroll_items ----------
    """
    CREATE TABLE IF NOT EXISTS hr_payroll_items (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        payroll_id UUID NOT NULL REFERENCES hr_payrolls(id) ON DELETE CASCADE,
        concept_id UUID REFERENCES hr_payroll_concepts(id) ON DELETE SET NULL,
        concept_code VARCHAR(40) NOT NULL,
        concept_name VARCHAR(150) NOT NULL,
        concept_type VARCHAR(30) NOT NULL,
        category VARCHAR(40),
        quantity NUMERIC(10,2),
        rate NUMERIC(14,4),
        base_amount NUMERIC(15,2),
        percentage NUMERIC(8,4),
        amount NUMERIC(15,2) NOT NULL,
        notes TEXT,
        sort_order INTEGER NOT NULL DEFAULT 100,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_payroll_items_payroll ON hr_payroll_items(payroll_id, sort_order)",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyHR · setup DDL fase 3 (nómina completa)")
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
