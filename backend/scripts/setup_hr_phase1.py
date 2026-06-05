"""DDL setup para SavvyHR fase 1 — estructura + empleados + contratos + documentos.

Idempotente. Multi-país: las orgs configuran su country_code en organizations.settings.

Tablas:
  - hr_departments         (jerárquicos)
  - hr_positions           (cargos con escala salarial)
  - hr_employees           (extiende people)
  - hr_contracts           (contratos laborales con vigencia)
  - hr_employee_documents  (HV, contratos, afiliaciones, exámenes)
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
    # ---------- hr_departments ----------
    """
    CREATE TABLE IF NOT EXISTS hr_departments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        parent_id UUID REFERENCES hr_departments(id) ON DELETE SET NULL,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        cost_center VARCHAR(40),
        manager_employee_id UUID,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_departments_org_code UNIQUE (organization_id, code)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_departments_org ON hr_departments(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_hr_departments_parent ON hr_departments(parent_id)",

    # ---------- hr_positions ----------
    """
    CREATE TABLE IF NOT EXISTS hr_positions (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        department_id UUID REFERENCES hr_departments(id) ON DELETE SET NULL,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(150) NOT NULL,
        description TEXT,
        level INTEGER,
        min_salary NUMERIC(14,2),
        max_salary NUMERIC(14,2),
        reference_salary NUMERIC(14,2),
        currency VARCHAR(3) NOT NULL DEFAULT 'COP',
        headcount_budget INTEGER,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_positions_org_code UNIQUE (organization_id, code)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_positions_org ON hr_positions(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_hr_positions_dept ON hr_positions(department_id)",

    # ---------- hr_employees ----------
    """
    CREATE TABLE IF NOT EXISTS hr_employees (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        person_id UUID REFERENCES people(id) ON DELETE SET NULL,
        employee_code VARCHAR(40) NOT NULL,
        first_name VARCHAR(100) NOT NULL,
        last_name VARCHAR(100),
        document_type VARCHAR(10),
        document_number VARCHAR(50),
        birth_date DATE,
        gender VARCHAR(10),
        marital_status VARCHAR(20),
        email VARCHAR(255),
        phone VARCHAR(50),
        mobile VARCHAR(50),
        address VARCHAR(255),
        city VARCHAR(100),
        country_code VARCHAR(3),
        emergency_contact_name VARCHAR(150),
        emergency_contact_phone VARCHAR(50),
        emergency_contact_relationship VARCHAR(40),
        department_id UUID REFERENCES hr_departments(id) ON DELETE SET NULL,
        position_id UUID REFERENCES hr_positions(id) ON DELETE SET NULL,
        supervisor_id UUID REFERENCES hr_employees(id) ON DELETE SET NULL,
        hire_date DATE NOT NULL,
        termination_date DATE,
        termination_reason VARCHAR(255),
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        employment_type VARCHAR(20) NOT NULL DEFAULT 'full_time',
        work_location VARCHAR(20) NOT NULL DEFAULT 'onsite',
        user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        notes TEXT,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_employees_org_code UNIQUE (organization_id, employee_code),
        CONSTRAINT uq_hr_employees_org_person UNIQUE (organization_id, person_id),
        CONSTRAINT chk_hr_employees_status CHECK (
            status IN ('active','on_leave','suspended','terminated')
        ),
        CONSTRAINT chk_hr_employees_employment_type CHECK (
            employment_type IN ('full_time','part_time','intern','contractor','temporary')
        ),
        CONSTRAINT chk_hr_employees_work_location CHECK (
            work_location IN ('onsite','remote','hybrid')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_employees_org ON hr_employees(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_hr_employees_dept ON hr_employees(department_id)",
    "CREATE INDEX IF NOT EXISTS ix_hr_employees_pos ON hr_employees(position_id)",
    "CREATE INDEX IF NOT EXISTS ix_hr_employees_status ON hr_employees(organization_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_hr_employees_supervisor ON hr_employees(supervisor_id)",

    # FK del manager del depto al empleado (deferred porque tabla creada arriba)
    """
    DO $$
    BEGIN
        IF NOT EXISTS (
            SELECT 1 FROM pg_constraint WHERE conname = 'fk_hr_departments_manager'
        ) THEN
            ALTER TABLE hr_departments
              ADD CONSTRAINT fk_hr_departments_manager
              FOREIGN KEY (manager_employee_id) REFERENCES hr_employees(id) ON DELETE SET NULL;
        END IF;
    END $$;
    """,

    # ---------- hr_contracts ----------
    """
    CREATE TABLE IF NOT EXISTS hr_contracts (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
        contract_number VARCHAR(40) NOT NULL,
        contract_type VARCHAR(30) NOT NULL,
        start_date DATE NOT NULL,
        end_date DATE,
        trial_period_end DATE,
        renewal_count INTEGER NOT NULL DEFAULT 0,
        base_salary NUMERIC(14,2) NOT NULL DEFAULT 0,
        currency VARCHAR(3) NOT NULL DEFAULT 'COP',
        payment_frequency VARCHAR(20) NOT NULL DEFAULT 'monthly',
        weekly_hours NUMERIC(5,2) NOT NULL DEFAULT 48,
        transport_allowance NUMERIC(14,2) NOT NULL DEFAULT 0,
        food_allowance NUMERIC(14,2) NOT NULL DEFAULT 0,
        connectivity_allowance NUMERIC(14,2) NOT NULL DEFAULT 0,
        other_allowance NUMERIC(14,2) NOT NULL DEFAULT 0,
        risk_class VARCHAR(10),
        eps_provider VARCHAR(150),
        pension_provider VARCHAR(150),
        severance_provider VARCHAR(150),
        compensation_fund VARCHAR(150),
        bank_name VARCHAR(80),
        bank_account_type VARCHAR(20),
        bank_account_number VARCHAR(40),
        status VARCHAR(20) NOT NULL DEFAULT 'active',
        terminated_at TIMESTAMPTZ,
        termination_reason VARCHAR(255),
        notes TEXT,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_contracts_org_number UNIQUE (organization_id, contract_number),
        CONSTRAINT chk_hr_contracts_type CHECK (
            contract_type IN ('indefinido','fijo','obra_labor','prestacion','aprendiz','practicante','otro')
        ),
        CONSTRAINT chk_hr_contracts_frequency CHECK (
            payment_frequency IN ('monthly','biweekly','weekly')
        ),
        CONSTRAINT chk_hr_contracts_status CHECK (
            status IN ('draft','active','suspended','terminated','expired')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_contracts_org ON hr_contracts(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_hr_contracts_employee ON hr_contracts(employee_id, status)",

    # ---------- hr_employee_documents ----------
    """
    CREATE TABLE IF NOT EXISTS hr_employee_documents (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
        document_type VARCHAR(40) NOT NULL,
        title VARCHAR(255) NOT NULL,
        description TEXT,
        file_url TEXT,
        file_size_bytes INTEGER,
        issue_date DATE,
        expiration_date DATE,
        issuer VARCHAR(150),
        reference_code VARCHAR(100),
        status VARCHAR(20) NOT NULL DEFAULT 'valid',
        uploaded_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_hr_doc_status CHECK (
            status IN ('valid','expired','revoked','pending_review')
        ),
        CONSTRAINT chk_hr_doc_type CHECK (
            document_type IN (
                'resume','contract','id_copy','tax_id',
                'eps_affiliation','pension_affiliation','severance_affiliation','arl_affiliation','compensation_fund_affiliation',
                'medical_exam','background_check','study_certificate','work_certificate',
                'training_certificate','disciplinary_record','other'
            )
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_doc_employee ON hr_employee_documents(employee_id, document_type)",
    "CREATE INDEX IF NOT EXISTS ix_hr_doc_org ON hr_employee_documents(organization_id)",
    "CREATE INDEX IF NOT EXISTS ix_hr_doc_expiration ON hr_employee_documents(organization_id, expiration_date) WHERE expiration_date IS NOT NULL",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyHR · setup DDL fase 1 (estructura + empleados + contratos + docs)")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, start=1):
            label = stmt.strip().splitlines()[0][:80]
            print(f"  [{i:2d}/{len(DDL)}] {label}")
            await s.execute(text(stmt))
        await s.commit()
    print("\nOK — schema fase 1 listo.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
