"""DDL setup para SavvyHR fase 4 — evaluaciones + capacitaciones.

Tablas:
  - hr_evaluation_cycles      (ciclos: plantilla de competencias + escala)
  - hr_evaluations            (una por empleado por ciclo)
  - hr_evaluation_responses   (respuesta individual: auto, jefe, 360°)
  - hr_training_courses       (catálogo de capacitaciones)
  - hr_training_enrollments   (inscripciones del empleado en un curso)
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
    # ---------- hr_evaluation_cycles ----------
    """
    CREATE TABLE IF NOT EXISTS hr_evaluation_cycles (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        period_label VARCHAR(40),
        start_date DATE NOT NULL,
        end_date DATE NOT NULL,
        enable_self BOOLEAN NOT NULL DEFAULT TRUE,
        enable_supervisor BOOLEAN NOT NULL DEFAULT TRUE,
        enable_360 BOOLEAN NOT NULL DEFAULT FALSE,
        scale_min NUMERIC(5,2) NOT NULL DEFAULT 1,
        scale_max NUMERIC(5,2) NOT NULL DEFAULT 5,
        competencies JSONB NOT NULL DEFAULT '[]'::jsonb,
        status VARCHAR(20) NOT NULL DEFAULT 'draft',
        opened_at TIMESTAMPTZ,
        closed_at TIMESTAMPTZ,
        notes TEXT,
        created_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_eval_cycle_code UNIQUE (organization_id, code),
        CONSTRAINT chk_hr_eval_cycle_status CHECK (
            status IN ('draft','open','closed','cancelled')
        ),
        CONSTRAINT chk_hr_eval_cycle_dates CHECK (end_date >= start_date)
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_eval_cycles_org ON hr_evaluation_cycles(organization_id, status)",

    # ---------- hr_evaluations ----------
    """
    CREATE TABLE IF NOT EXISTS hr_evaluations (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        cycle_id UUID NOT NULL REFERENCES hr_evaluation_cycles(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
        supervisor_id UUID REFERENCES hr_employees(id) ON DELETE SET NULL,
        self_completed BOOLEAN NOT NULL DEFAULT FALSE,
        self_score NUMERIC(5,2),
        supervisor_completed BOOLEAN NOT NULL DEFAULT FALSE,
        supervisor_score NUMERIC(5,2),
        peer_count INTEGER NOT NULL DEFAULT 0,
        peer_avg NUMERIC(5,2),
        overall_score NUMERIC(5,2),
        status VARCHAR(20) NOT NULL DEFAULT 'pending',
        completed_at TIMESTAMPTZ,
        improvement_plan TEXT,
        notes TEXT,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_eval_cycle_emp UNIQUE (cycle_id, employee_id),
        CONSTRAINT chk_hr_eval_status CHECK (
            status IN ('pending','in_progress','completed','cancelled')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_evaluations_emp ON hr_evaluations(employee_id, status)",
    "CREATE INDEX IF NOT EXISTS ix_hr_evaluations_cycle ON hr_evaluations(cycle_id)",

    # ---------- hr_evaluation_responses ----------
    """
    CREATE TABLE IF NOT EXISTS hr_evaluation_responses (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        evaluation_id UUID NOT NULL REFERENCES hr_evaluations(id) ON DELETE CASCADE,
        evaluator_type VARCHAR(20) NOT NULL,
        evaluator_user_id UUID REFERENCES users(id) ON DELETE SET NULL,
        evaluator_employee_id UUID REFERENCES hr_employees(id) ON DELETE SET NULL,
        scores JSONB NOT NULL DEFAULT '{}'::jsonb,
        overall_score NUMERIC(5,2),
        comments TEXT,
        submitted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_hr_eval_resp_type CHECK (
            evaluator_type IN ('self','supervisor','peer','subordinate')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_eval_resp_eval ON hr_evaluation_responses(evaluation_id, evaluator_type)",

    # ---------- hr_training_courses ----------
    """
    CREATE TABLE IF NOT EXISTS hr_training_courses (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        code VARCHAR(40) NOT NULL,
        name VARCHAR(200) NOT NULL,
        description TEXT,
        category VARCHAR(40) NOT NULL DEFAULT 'general',
        duration_hours NUMERIC(6,2),
        delivery_mode VARCHAR(20) NOT NULL DEFAULT 'in_person',
        is_mandatory BOOLEAN NOT NULL DEFAULT FALSE,
        provider VARCHAR(150),
        cost_per_seat NUMERIC(14,2),
        certificate_template_url TEXT,
        is_active BOOLEAN NOT NULL DEFAULT TRUE,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT uq_hr_training_courses_code UNIQUE (organization_id, code),
        CONSTRAINT chk_hr_training_mode CHECK (
            delivery_mode IN ('in_person','virtual_live','virtual_async','hybrid','external')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_training_courses_org ON hr_training_courses(organization_id, is_active)",

    # ---------- hr_training_enrollments ----------
    """
    CREATE TABLE IF NOT EXISTS hr_training_enrollments (
        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
        organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
        course_id UUID NOT NULL REFERENCES hr_training_courses(id) ON DELETE CASCADE,
        employee_id UUID NOT NULL REFERENCES hr_employees(id) ON DELETE CASCADE,
        scheduled_date DATE,
        completed_date DATE,
        completion_status VARCHAR(20) NOT NULL DEFAULT 'enrolled',
        score NUMERIC(5,2),
        attendance_pct NUMERIC(5,2),
        certificate_url TEXT,
        certificate_number VARCHAR(80),
        cost NUMERIC(14,2),
        notes TEXT,
        enrolled_by UUID REFERENCES users(id) ON DELETE SET NULL,
        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
        CONSTRAINT chk_hr_training_enr_status CHECK (
            completion_status IN ('enrolled','in_progress','completed','failed','cancelled')
        )
    )
    """,
    "CREATE INDEX IF NOT EXISTS ix_hr_training_enr_emp ON hr_training_enrollments(employee_id, completion_status)",
    "CREATE INDEX IF NOT EXISTS ix_hr_training_enr_course ON hr_training_enrollments(course_id)",
]


async def main() -> None:
    print("=" * 70)
    print("SavvyHR · setup DDL fase 4 (evaluaciones + capacitaciones)")
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
