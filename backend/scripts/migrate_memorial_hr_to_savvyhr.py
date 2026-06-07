"""Migración idempotente Memorial.hr → SavvyHR.

Lee `memorial_positions`, `memorial_employees` y `memorial_attendance` y los
copia a las tablas equivalentes de SavvyHR (`hr_positions`, `hr_employees`,
`hr_contracts` —contrato base auto-generado—, `hr_attendance`).

Idempotente: usa `(organization_id, code/employee_code)` como llave para
detectar registros ya migrados y los actualiza en lugar de duplicar.

Uso:
    python backend/scripts/migrate_memorial_hr_to_savvyhr.py
    python backend/scripts/migrate_memorial_hr_to_savvyhr.py --org <org_id>
    python backend/scripts/migrate_memorial_hr_to_savvyhr.py --dry-run

Después de validar el resultado, las tablas memorial_* pueden ser
removidas en una migración posterior. Por ahora se conservan para
posibilitar rollback.
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import uuid
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import text  # noqa: E402

from src.core.database import async_session_factory, engine  # noqa: E402


VALID_HR_ATT_STATUS = {
    "present", "absent", "late", "early_leave",
    "justified", "vacation", "sick_leave", "permit", "holiday",
}


async def _resolve_organizations(conn, only_org: uuid.UUID | None) -> list[uuid.UUID]:
    if only_org:
        return [only_org]
    rows = await conn.execute(text(
        "SELECT DISTINCT organization_id FROM memorial_employees"
    ))
    return [r[0] for r in rows.fetchall()]


async def _migrate_positions(conn, org_id: uuid.UUID, dry: bool) -> dict[uuid.UUID, uuid.UUID]:
    """memorial_positions → hr_positions. Devuelve mapeo old_id → new_id."""
    rows = await conn.execute(
        text(
            "SELECT id, code, name, description, is_active "
            "FROM memorial_positions WHERE organization_id = :org"
        ),
        {"org": org_id},
    )
    src = rows.fetchall()
    mapping: dict[uuid.UUID, uuid.UUID] = {}
    inserted = updated = 0
    for r in src:
        existing = (await conn.execute(
            text(
                "SELECT id FROM hr_positions "
                "WHERE organization_id = :org AND code = :code"
            ),
            {"org": org_id, "code": r.code},
        )).first()
        if existing:
            mapping[r.id] = existing[0]
            if not dry:
                await conn.execute(
                    text(
                        "UPDATE hr_positions SET name = :name, description = :desc, "
                        "is_active = :is_active, updated_at = NOW() WHERE id = :id"
                    ),
                    {"id": existing[0], "name": r.name, "desc": r.description, "is_active": r.is_active},
                )
            updated += 1
        else:
            new_id = uuid.uuid4()
            mapping[r.id] = new_id
            if not dry:
                await conn.execute(
                    text(
                        "INSERT INTO hr_positions "
                        "(id, organization_id, code, name, description, currency, is_active, created_at, updated_at) "
                        "VALUES (:id, :org, :code, :name, :desc, 'COP', :is_active, NOW(), NOW())"
                    ),
                    {
                        "id": new_id, "org": org_id, "code": r.code, "name": r.name,
                        "desc": r.description, "is_active": r.is_active,
                    },
                )
            inserted += 1
    print(f"  · positions: {inserted} insertados, {updated} actualizados")
    return mapping


async def _migrate_employees(
    conn, org_id: uuid.UUID, position_map: dict[uuid.UUID, uuid.UUID], dry: bool,
) -> dict[uuid.UUID, uuid.UUID]:
    """memorial_employees → hr_employees + contrato base. Devuelve mapeo old_id → new_id."""
    rows = await conn.execute(
        text(
            "SELECT id, code, first_name, last_name, document_type, document_number, "
            "birth_date, gender, email, phone, mobile, address, position_id, "
            "contract_type, hire_date, end_date, base_salary, default_shift, status, "
            "user_id, notes "
            "FROM memorial_employees WHERE organization_id = :org"
        ),
        {"org": org_id},
    )
    src = rows.fetchall()
    mapping: dict[uuid.UUID, uuid.UUID] = {}
    inserted = updated = contracts_created = 0
    for r in src:
        new_position_id = position_map.get(r.position_id) if r.position_id else None
        existing = (await conn.execute(
            text(
                "SELECT id FROM hr_employees "
                "WHERE organization_id = :org AND employee_code = :code"
            ),
            {"org": org_id, "code": r.code},
        )).first()
        if existing:
            emp_id = existing[0]
            mapping[r.id] = emp_id
            if not dry:
                await conn.execute(
                    text(
                        "UPDATE hr_employees SET "
                        "first_name = :fn, last_name = :ln, "
                        "document_type = :dt, document_number = :dn, "
                        "birth_date = :bd, gender = :g, "
                        "email = :em, phone = :ph, mobile = :mob, address = :ad, "
                        "position_id = :pos, hire_date = :hd, "
                        "termination_date = :td, status = :st, "
                        "user_id = COALESCE(:uid, user_id), notes = :nt, updated_at = NOW() "
                        "WHERE id = :id"
                    ),
                    {
                        "id": emp_id, "fn": r.first_name, "ln": r.last_name,
                        "dt": r.document_type, "dn": r.document_number,
                        "bd": r.birth_date, "g": r.gender,
                        "em": r.email, "ph": r.phone, "mob": r.mobile, "ad": r.address,
                        "pos": new_position_id, "hd": r.hire_date,
                        "td": r.end_date, "st": r.status,
                        "uid": r.user_id, "nt": r.notes,
                    },
                )
            updated += 1
        else:
            emp_id = uuid.uuid4()
            mapping[r.id] = emp_id
            if not dry:
                await conn.execute(
                    text(
                        "INSERT INTO hr_employees "
                        "(id, organization_id, employee_code, first_name, last_name, "
                        "document_type, document_number, birth_date, gender, "
                        "email, phone, mobile, address, position_id, hire_date, "
                        "termination_date, status, employment_type, work_location, "
                        "user_id, notes, created_at, updated_at) "
                        "VALUES (:id, :org, :code, :fn, :ln, :dt, :dn, :bd, :g, "
                        ":em, :ph, :mob, :ad, :pos, :hd, :td, :st, "
                        "'full_time', 'onsite', :uid, :nt, NOW(), NOW())"
                    ),
                    {
                        "id": emp_id, "org": org_id, "code": r.code,
                        "fn": r.first_name, "ln": r.last_name,
                        "dt": r.document_type, "dn": r.document_number,
                        "bd": r.birth_date, "g": r.gender,
                        "em": r.email, "ph": r.phone, "mob": r.mobile, "ad": r.address,
                        "pos": new_position_id, "hd": r.hire_date,
                        "td": r.end_date, "st": r.status,
                        "uid": r.user_id, "nt": r.notes,
                    },
                )
            inserted += 1

        # Contrato base si no existe
        salary = Decimal(r.base_salary or 0)
        has_contract = (await conn.execute(
            text("SELECT 1 FROM hr_contracts WHERE employee_id = :emp LIMIT 1"),
            {"emp": emp_id},
        )).first()
        if not has_contract and salary > 0:
            if not dry:
                contract_number = f"MIG-{r.code}"
                await conn.execute(
                    text(
                        "INSERT INTO hr_contracts "
                        "(id, organization_id, employee_id, contract_number, "
                        "contract_type, start_date, end_date, base_salary, "
                        "currency, payment_frequency, weekly_hours, "
                        "transport_allowance, food_allowance, "
                        "connectivity_allowance, other_allowance, renewal_count, "
                        "status, created_at, updated_at) "
                        "VALUES (:id, :org, :emp, :cn, :ct, :sd, :ed, :bs, "
                        "'COP', 'monthly', 48, 0, 0, 0, 0, 0, :status, NOW(), NOW())"
                    ),
                    {
                        "id": uuid.uuid4(), "org": org_id, "emp": emp_id,
                        "cn": contract_number,
                        "ct": r.contract_type or "indefinido",
                        "sd": r.hire_date, "ed": r.end_date, "bs": salary,
                        "status": "terminated" if r.end_date else "active",
                    },
                )
            contracts_created += 1
    print(
        f"  · employees: {inserted} insertados, {updated} actualizados, "
        f"{contracts_created} contratos base creados"
    )
    return mapping


async def _migrate_attendance(
    conn, org_id: uuid.UUID, employee_map: dict[uuid.UUID, uuid.UUID], dry: bool,
) -> None:
    rows = await conn.execute(
        text(
            "SELECT id, employee_id, work_date, check_in_at, check_out_at, "
            "hours_worked, status, notes, recorded_by "
            "FROM memorial_attendance WHERE organization_id = :org"
        ),
        {"org": org_id},
    )
    src = rows.fetchall()
    inserted = updated = skipped = 0
    for r in src:
        new_emp_id = employee_map.get(r.employee_id)
        if not new_emp_id:
            skipped += 1
            continue
        status = r.status if r.status in VALID_HR_ATT_STATUS else "present"
        existing = (await conn.execute(
            text(
                "SELECT id FROM hr_attendance "
                "WHERE employee_id = :emp AND work_date = :wd"
            ),
            {"emp": new_emp_id, "wd": r.work_date},
        )).first()
        if existing:
            if not dry:
                await conn.execute(
                    text(
                        "UPDATE hr_attendance SET "
                        "check_in_at = :ci, check_out_at = :co, "
                        "worked_hours = :wh, status = :st, notes = :nt, "
                        "recorded_by = COALESCE(:rb, recorded_by), updated_at = NOW() "
                        "WHERE id = :id"
                    ),
                    {
                        "id": existing[0],
                        "ci": r.check_in_at, "co": r.check_out_at,
                        "wh": r.hours_worked, "st": status, "nt": r.notes,
                        "rb": r.recorded_by,
                    },
                )
            updated += 1
        else:
            if not dry:
                await conn.execute(
                    text(
                        "INSERT INTO hr_attendance "
                        "(id, organization_id, employee_id, work_date, "
                        "check_in_at, check_out_at, worked_hours, "
                        "overtime_day_hours, overtime_night_hours, overtime_holiday_hours, "
                        "status, notes, recorded_by, created_at, updated_at) "
                        "VALUES (:id, :org, :emp, :wd, :ci, :co, :wh, "
                        "0, 0, 0, :st, :nt, :rb, NOW(), NOW())"
                    ),
                    {
                        "id": uuid.uuid4(), "org": org_id, "emp": new_emp_id,
                        "wd": r.work_date, "ci": r.check_in_at, "co": r.check_out_at,
                        "wh": r.hours_worked, "st": status, "nt": r.notes,
                        "rb": r.recorded_by,
                    },
                )
            inserted += 1
    print(
        f"  · attendance: {inserted} insertados, {updated} actualizados, "
        f"{skipped} omitidos (empleado huérfano)"
    )


async def _ensure_app_enrolled(conn, org_id: uuid.UUID, dry: bool) -> None:
    """Habilita el app `hr` en la organización si aún no está."""
    app_id = (await conn.execute(
        text("SELECT id FROM app_registry WHERE code = 'hr'"),
    )).first()
    if not app_id:
        print("  ⚠ App 'hr' no registrado todavía. Ejecuta seed_hr_app.py primero.")
        return
    existing = (await conn.execute(
        text(
            "SELECT 1 FROM organization_apps "
            "WHERE organization_id = :org AND app_id = :app"
        ),
        {"org": org_id, "app": app_id[0]},
    )).first()
    if existing:
        return
    if not dry:
        await conn.execute(
            text(
                "INSERT INTO organization_apps "
                "(id, organization_id, app_id, status, activated_at, created_at, updated_at) "
                "VALUES (:id, :org, :app, 'active', NOW(), NOW(), NOW())"
            ),
            {"id": uuid.uuid4(), "org": org_id, "app": app_id[0]},
        )
    print("  · app 'hr' habilitado para la organización")


async def migrate(only_org: uuid.UUID | None, dry: bool) -> None:
    async with async_session_factory() as session:
        async with session.begin():
            conn = await session.connection()
            orgs = await _resolve_organizations(conn, only_org)
            if not orgs:
                print("Sin organizaciones que migrar (memorial_employees vacío).")
                return
            print(f"Migrando {len(orgs)} organización(es). dry={dry}\n")
            for org_id in orgs:
                print(f"▶ Organización {org_id}")
                await _ensure_app_enrolled(conn, org_id, dry)
                pmap = await _migrate_positions(conn, org_id, dry)
                emap = await _migrate_employees(conn, org_id, pmap, dry)
                await _migrate_attendance(conn, org_id, emap, dry)
                print()
            if dry:
                await session.rollback()
                print("DRY-RUN — ningún cambio persistido.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Migrar Memorial.hr → SavvyHR")
    parser.add_argument("--org", type=str, help="UUID de organización específica")
    parser.add_argument("--dry-run", action="store_true", help="Simular sin escribir")
    args = parser.parse_args()
    only_org = uuid.UUID(args.org) if args.org else None
    try:
        asyncio.run(migrate(only_org, args.dry_run))
    finally:
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
