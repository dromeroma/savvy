"""Seed idempotente del app `hr` en app_registry + permisos + roles del sistema.

Corre después de aplicar setup_hr_phase1.py.
"""

from __future__ import annotations

import asyncio
import logging
import sys
import uuid
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import text  # noqa: E402

from src.core.database import async_session_factory, engine  # noqa: E402


APP_CODE = "hr"
APP_NAME = "SavvyHR"
APP_DESCRIPTION = (
    "Talento humano: empleados, contratos, asistencia, vacaciones, "
    "nómina, prestaciones, evaluaciones de desempeño y capacitaciones."
)
APP_ICON = "users"
APP_COLOR = "#EC4899"

PERMISSIONS = [
    ("hr.read", "Ver datos de RRHH", "read"),
    ("hr.employees.manage", "Gestionar empleados (crear/editar/eliminar)", "employees"),
    ("hr.contracts.manage", "Gestionar contratos laborales", "contracts"),
    ("hr.attendance.manage", "Gestionar asistencia y turnos", "attendance"),
    ("hr.vacations.manage", "Gestionar vacaciones (todos los empleados)", "vacations"),
    ("hr.vacations.approve", "Aprobar/rechazar solicitudes de vacaciones", "vacations"),
    ("hr.leaves.manage", "Gestionar incapacidades y permisos", "leaves"),
    ("hr.payroll.run", "Liquidar nómina", "payroll"),
    ("hr.payroll.approve", "Aprobar y cerrar nómina", "payroll"),
    ("hr.evaluations.manage", "Administrar ciclos de evaluación", "evaluations"),
    ("hr.evaluations.respond", "Responder evaluación propia", "evaluations"),
    ("hr.training.manage", "Administrar capacitaciones", "training"),
    ("hr.confidential.read", "Ver datos sensibles (salarios, evaluaciones de otros)", "confidential"),
]

ROLES = [
    ("owner", "Owner / Propietario", [
        "hr.read", "hr.employees.manage", "hr.contracts.manage",
        "hr.attendance.manage", "hr.vacations.manage", "hr.vacations.approve",
        "hr.leaves.manage", "hr.payroll.run", "hr.payroll.approve",
        "hr.evaluations.manage", "hr.evaluations.respond",
        "hr.training.manage", "hr.confidential.read",
    ]),
    ("hr_manager", "Jefe de RRHH", [
        "hr.read", "hr.employees.manage", "hr.contracts.manage",
        "hr.attendance.manage", "hr.vacations.manage", "hr.vacations.approve",
        "hr.leaves.manage", "hr.payroll.run",
        "hr.evaluations.manage", "hr.training.manage", "hr.confidential.read",
    ]),
    ("hr_specialist", "Especialista RRHH", [
        "hr.read", "hr.employees.manage", "hr.contracts.manage",
        "hr.attendance.manage", "hr.vacations.manage",
        "hr.leaves.manage", "hr.training.manage",
    ]),
    ("payroll_runner", "Liquidador de nómina", [
        "hr.read", "hr.payroll.run", "hr.confidential.read",
    ]),
    ("employee_self_service", "Empleado (auto-servicio)", [
        "hr.read", "hr.evaluations.respond",
    ]),
]


async def main() -> None:
    print("=" * 70)
    print("SavvyHR · seed app_registry + permisos + roles")
    print("=" * 70)
    async with async_session_factory() as s:
        # 1) AppRegistry
        existing = await s.execute(
            text("SELECT id FROM app_registry WHERE code = :c"),
            {"c": APP_CODE},
        )
        app_row = existing.first()
        if app_row is None:
            app_id = uuid.uuid4()
            await s.execute(
                text("""
                    INSERT INTO app_registry (id, code, name, description, icon, color, is_active, is_external)
                    VALUES (:id, :code, :name, :desc, :icon, :color, TRUE, FALSE)
                """),
                {
                    "id": app_id, "code": APP_CODE, "name": APP_NAME,
                    "desc": APP_DESCRIPTION, "icon": APP_ICON, "color": APP_COLOR,
                },
            )
            print(f"  + app_registry: {APP_NAME} ({APP_CODE})")
        else:
            app_id = app_row[0]
            await s.execute(
                text("""
                    UPDATE app_registry
                    SET name = :name, description = :desc, icon = :icon, color = :color, is_active = TRUE
                    WHERE id = :id
                """),
                {
                    "id": app_id, "name": APP_NAME, "desc": APP_DESCRIPTION,
                    "icon": APP_ICON, "color": APP_COLOR,
                },
            )
            print(f"  ~ app_registry: {APP_NAME} (actualizado)")

        # 2) Permission catalog
        for code, label, category in PERMISSIONS:
            exists = await s.scalar(
                text("SELECT 1 FROM app_permission_catalog WHERE app_code = :a AND code = :c"),
                {"a": APP_CODE, "c": code},
            )
            if exists is None:
                await s.execute(
                    text("""
                        INSERT INTO app_permission_catalog (id, app_code, code, name, category)
                        VALUES (gen_random_uuid(), :a, :c, :l, :cat)
                    """),
                    {"a": APP_CODE, "c": code, "l": label, "cat": category},
                )
        print(f"  + {len(PERMISSIONS)} permisos en app_permission_catalog")

        # 3) Role catalog (sistema)
        for code, label, perms in ROLES:
            exists = await s.scalar(
                text("""
                    SELECT id FROM app_role_catalog
                    WHERE app_code = :a AND code = :c AND organization_id IS NULL
                """),
                {"a": APP_CODE, "c": code},
            )
            if exists is None:
                await s.execute(
                    text("""
                        INSERT INTO app_role_catalog (id, app_code, code, name, permissions, organization_id)
                        VALUES (gen_random_uuid(), :a, :c, :n, cast(:p as jsonb), NULL)
                    """),
                    {"a": APP_CODE, "c": code, "n": label, "p": _json(perms)},
                )
            else:
                await s.execute(
                    text("""
                        UPDATE app_role_catalog
                        SET name = :n, permissions = cast(:p as jsonb)
                        WHERE id = :id
                    """),
                    {"id": exists, "n": label, "p": _json(perms)},
                )
        print(f"  + {len(ROLES)} roles del sistema en app_role_catalog")

        await s.commit()
    print("\nOK — hr registrado.")
    await engine.dispose()


def _json(lst):
    import json
    return json.dumps(lst)


if __name__ == "__main__":
    asyncio.run(main())
