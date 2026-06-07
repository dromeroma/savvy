"""Seed idempotente de SavvyHR para Funeraria San Rafael (memorial-demo).

Rellena todos los submódulos con datos coherentes para demo:
  - 3 departamentos (Operaciones · Administración · Comercial)
  - 3 turnos (Diurno · Nocturno velación · Administrativo)
  - 19 conceptos de nómina Colombia
  - 2 períodos liquidados (mayo + abril 2026)
  - 16 payrolls + ~120 items
  - Saldos de vacaciones 2026 + 2 solicitudes
  - 2 incapacidades (1 activa, 1 completada)
  - 1 ciclo de evaluación con 8 evaluaciones (auto+jefe)
  - 3 cursos de capacitación + matrículas
  - Documentos por empleado
  - hr_settings con plantilla default 'formal' y branding

Uso:
    python backend/scripts/seed_hr_san_rafael.py
    python backend/scripts/seed_hr_san_rafael.py --dry-run
"""

from __future__ import annotations

import argparse
import asyncio
import json
import logging
import sys
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import text  # noqa: E402

from src.core.database import async_session_factory, engine  # noqa: E402


ORG_SLUG = "memorial-demo"


# ============================================================ Catálogos

DEPARTMENTS = [
    ("OPS", "Operaciones", "Personal de campo: conductores, auxiliares, atención de servicios"),
    ("ADM", "Administración", "Personal administrativo, contabilidad y dirección"),
    ("COM", "Comercial", "Asesores comerciales y gestión de planes exequiales"),
]

SHIFTS = [
    ("SH-DIURNO", "Diurno operacional", "morning", time(8, 0), time(17, 0), 60, [1, 2, 3, 4, 5], "44.00"),
    ("SH-NOCTURNO", "Velación nocturna", "night", time(18, 0), time(6, 0), 120, [1, 2, 3, 4, 5, 6, 7], "84.00"),
    ("SH-ADMIN", "Administrativo", "administrative", time(8, 0), time(16, 0), 60, [1, 2, 3, 4, 5], "40.00"),
]


# Mapeo empleado → (departamento_code, shift_code, supervisor_emp_code)
EMPLOYEE_ASSIGN = {
    "DIR-001": ("ADM", "SH-ADMIN", None),
    "COORD-001": ("OPS", "SH-DIURNO", "DIR-001"),
    "COORD-002": ("COM", "SH-ADMIN", "DIR-001"),
    "AUX-001": ("OPS", "SH-DIURNO", "COORD-001"),
    "AUX-002": ("OPS", "SH-DIURNO", "COORD-001"),
    "AUX-003": ("OPS", "SH-NOCTURNO", "COORD-001"),
    "COND-001": ("OPS", "SH-DIURNO", "COORD-001"),
    "COND-002": ("OPS", "SH-NOCTURNO", "COORD-001"),
}


# Conceptos de nómina Colombia (subset esencial)
CONCEPTS = [
    # code, name, type, category, method, formula/pct/fixed, sort_order
    ("SUELDO", "Sueldo básico", "earning", "salary", "fixed", None, None, None, 10),
    ("AUX_TRANS", "Auxilio de transporte", "earning", "allowance", "fixed", None, None, "162000", 20),
    ("HE_DIU", "Horas extra diurnas", "earning", "overtime", "quantity_rate", None, None, None, 30),
    ("HE_NOC", "Horas extra nocturnas", "earning", "overtime", "quantity_rate", None, None, None, 31),
    ("BONIFIC", "Bonificación de desempeño", "earning", "bonus", "fixed", None, None, None, 40),
    ("SALUD_EMP", "Aporte salud empleado", "deduction", "social_security", "percentage", None, "4.00", None, 100),
    ("PENSION_EMP", "Aporte pensión empleado", "deduction", "social_security", "percentage", None, "4.00", None, 101),
    ("FONDO_SOL", "Fondo de solidaridad", "deduction", "social_security", "percentage", None, "1.00", None, 102),
    ("RETEFUENTE", "Retención en la fuente", "deduction", "tax", "fixed", None, None, "0", 110),
    ("PRESTAMO", "Descuento préstamo interno", "deduction", "other", "fixed", None, None, "0", 120),
    ("CESANTIAS", "Cesantías", "benefit", "severance", "percentage", None, "8.33", None, 200),
    ("INT_CES", "Intereses cesantías", "benefit", "severance", "percentage", None, "1.00", None, 201),
    ("PRIMA", "Prima de servicios", "benefit", "premium", "percentage", None, "8.33", None, 202),
    ("VACACIONES", "Vacaciones causadas", "benefit", "vacation", "percentage", None, "4.17", None, 203),
    ("SALUD_PAT", "Aporte salud patronal", "employer_contribution", "social_security", "percentage", None, "8.50", None, 300),
    ("PENSION_PAT", "Aporte pensión patronal", "employer_contribution", "social_security", "percentage", None, "12.00", None, 301),
    ("ARL", "Aporte ARL", "employer_contribution", "social_security", "percentage", None, "0.522", None, 302),
    ("CAJA", "Caja de compensación", "employer_contribution", "parafiscal", "percentage", None, "4.00", None, 303),
    ("ICBF_SENA", "Aporte ICBF + SENA", "employer_contribution", "parafiscal", "percentage", None, "5.00", None, 304),
]


# Plantilla de competencias para el ciclo de evaluación
COMPETENCIES = [
    {"code": "atencion", "name": "Atención a familias", "weight": 30,
     "description": "Empatía, escucha activa y manejo del duelo durante el servicio funerario"},
    {"code": "bioseguridad", "name": "Cumplimiento de bioseguridad", "weight": 25,
     "description": "Uso de EPP, manejo de tanatopraxia, protocolos sanitarios"},
    {"code": "trabajo_equipo", "name": "Trabajo en equipo", "weight": 20,
     "description": "Colaboración con colegas, comunicación interna y disposición"},
    {"code": "puntualidad", "name": "Puntualidad y disciplina", "weight": 15,
     "description": "Asistencia, cumplimiento de turnos y manejo del tiempo"},
    {"code": "iniciativa", "name": "Iniciativa", "weight": 10,
     "description": "Proactividad y propuesta de mejoras"},
]


# Cursos de capacitación
COURSES = [
    ("BIO-2026", "Bioseguridad y tanatopraxia 2026", "Curso obligatorio anual de bioseguridad para personal operativo",
     "obligatorio", "8.00", "in_person", True, "Inspectoría Departamental"),
    ("ATFAM-01", "Atención a familias en duelo", "Manejo emocional y comunicación con familias dolientes",
     "competencias", "12.00", "hybrid", False, "Universidad El Bosque"),
    ("SST-2026", "Sistema de Gestión SST", "Capacitación de seguridad y salud en el trabajo",
     "sst", "16.00", "virtual_async", True, "ARL Sura"),
]


# ============================================================ Helpers


def D(v) -> Decimal:
    return Decimal(str(v))


async def _exec(conn, sql, **params):
    return await conn.execute(text(sql), params)


async def _scalar(conn, sql, **params):
    return await conn.scalar(text(sql), params)


async def _fetch_all(conn, sql, **params):
    rows = await conn.execute(text(sql), params)
    return rows.fetchall()


# ============================================================ Seed steps


async def seed_org_settings(s, org_id: uuid.UUID, dry: bool):
    """Configuración HR de la organización (plantilla default + branding)."""
    existing = await _scalar(s, "SELECT id FROM hr_settings WHERE organization_id = :org", org=org_id)
    if existing:
        if not dry:
            await _exec(s, """
                UPDATE hr_settings SET
                  default_liquidation_template = 'formal',
                  liquidation_notes_default = :notes,
                  admin_name = :admin_name,
                  admin_title = :admin_title,
                  brand_color = :brand,
                  updated_at = NOW()
                WHERE id = :id
            """, id=existing, notes="Gracias por su servicio a Funeraria San Rafael.",
              admin_name="Roberto Salazar Vega", admin_title="Director General", brand="#8b5cf6")
        print("  · hr_settings: actualizado")
    else:
        if not dry:
            await _exec(s, """
                INSERT INTO hr_settings
                  (id, organization_id, default_liquidation_template, liquidation_notes_default,
                   admin_name, admin_title, brand_color, created_at, updated_at)
                VALUES (:id, :org, 'formal', :notes, :admin_name, :admin_title, :brand, NOW(), NOW())
            """, id=uuid.uuid4(), org=org_id,
              notes="Gracias por su servicio a Funeraria San Rafael.",
              admin_name="Roberto Salazar Vega", admin_title="Director General", brand="#8b5cf6")
        print("  · hr_settings: creado")


async def seed_departments(s, org_id: uuid.UUID, dry: bool) -> dict[str, uuid.UUID]:
    out: dict[str, uuid.UUID] = {}
    for code, name, desc in DEPARTMENTS:
        existing = await _scalar(s, """
            SELECT id FROM hr_departments WHERE organization_id = :org AND code = :code
        """, org=org_id, code=code)
        if existing:
            out[code] = existing
        else:
            new_id = uuid.uuid4()
            out[code] = new_id
            if not dry:
                await _exec(s, """
                    INSERT INTO hr_departments (id, organization_id, code, name, description,
                                                 is_active, created_at, updated_at)
                    VALUES (:id, :org, :code, :name, :desc, true, NOW(), NOW())
                """, id=new_id, org=org_id, code=code, name=name, desc=desc)
    print(f"  · departamentos: {len(out)} listos")
    return out


async def seed_shifts(s, org_id: uuid.UUID, dry: bool) -> dict[str, uuid.UUID]:
    out: dict[str, uuid.UUID] = {}
    for code, name, stype, start, end, brk, dow, hours in SHIFTS:
        existing = await _scalar(s, """
            SELECT id FROM hr_shifts WHERE organization_id = :org AND code = :code
        """, org=org_id, code=code)
        if existing:
            out[code] = existing
        else:
            new_id = uuid.uuid4()
            out[code] = new_id
            if not dry:
                await _exec(s, """
                    INSERT INTO hr_shifts
                      (id, organization_id, code, name, shift_type, start_time, end_time,
                       break_minutes, days_of_week, weekly_hours, is_active, created_at, updated_at)
                    VALUES (:id, :org, :code, :name, :st, :s, :e, :br, CAST(:dow AS JSONB),
                            :hrs, true, NOW(), NOW())
                """, id=new_id, org=org_id, code=code, name=name, st=stype,
                  s=start, e=end, br=brk, dow=json.dumps(dow), hrs=hours)
    print(f"  · turnos: {len(out)} listos")
    return out


async def assign_employees_to_dept_and_supervisor(
    s, org_id: uuid.UUID, dept_map: dict[str, uuid.UUID], dry: bool,
):
    """Asigna department_id + supervisor_id en hr_employees."""
    emps = await _fetch_all(s,
        "SELECT id, employee_code FROM hr_employees WHERE organization_id = :org", org=org_id,
    )
    code_to_id = {r.employee_code: r.id for r in emps}
    updates = 0
    for emp_code, (dept_code, _, sup_code) in EMPLOYEE_ASSIGN.items():
        if emp_code not in code_to_id:
            continue
        emp_id = code_to_id[emp_code]
        dept_id = dept_map.get(dept_code)
        sup_id = code_to_id.get(sup_code) if sup_code else None
        if not dry:
            await _exec(s, """
                UPDATE hr_employees SET department_id = :d, supervisor_id = :sup, updated_at = NOW()
                WHERE id = :id
            """, d=dept_id, sup=sup_id, id=emp_id)
        updates += 1
    print(f"  · asignación dept+supervisor: {updates}")
    return code_to_id


async def seed_concepts(s, org_id: uuid.UUID, dry: bool):
    inserted = 0
    for c in CONCEPTS:
        code, name, ctype, category, method, formula, pct, fixed, sort_order = c
        existing = await _scalar(s, """
            SELECT id FROM hr_payroll_concepts WHERE organization_id = :org AND code = :code
        """, org=org_id, code=code)
        if existing:
            continue
        if not dry:
            await _exec(s, """
                INSERT INTO hr_payroll_concepts
                  (id, organization_id, code, name, concept_type, category, calculation_method,
                   formula, percentage_value, fixed_value, country_code, is_taxable, is_active,
                   sort_order, created_at, updated_at)
                VALUES (:id, :org, :code, :name, :ctype, :cat, :method,
                        :formula, :pct, :fixed, 'CO', true, true, :so, NOW(), NOW())
            """, id=uuid.uuid4(), org=org_id, code=code, name=name, ctype=ctype, cat=category,
              method=method, formula=formula, pct=pct, fixed=fixed, so=sort_order)
        inserted += 1
    print(f"  · conceptos nómina: {inserted} nuevos (total objetivo {len(CONCEPTS)})")


async def seed_payroll_periods_and_runs(
    s, org_id: uuid.UUID, code_to_emp: dict[str, uuid.UUID], dry: bool,
):
    """Crea 2 períodos (abril + mayo 2026), un payroll por empleado con ítems calculados."""
    periods = [
        ("PAY-2026-04", "Nómina abril 2026", date(2026, 4, 1), date(2026, 4, 30), date(2026, 4, 30)),
        ("PAY-2026-05", "Nómina mayo 2026", date(2026, 5, 1), date(2026, 5, 31), date(2026, 5, 31)),
    ]
    # Cargar contratos y salario base por empleado
    contracts = await _fetch_all(s, """
        SELECT employee_id, base_salary, transport_allowance
        FROM hr_contracts
        WHERE organization_id = :org AND status IN ('active','draft','terminated')
    """, org=org_id)
    by_emp: dict[uuid.UUID, tuple[Decimal, Decimal]] = {}
    for c in contracts:
        by_emp[c.employee_id] = (D(c.base_salary or 0), D(c.transport_allowance or 0))

    periods_created = 0
    payrolls_created = 0
    items_created = 0
    for code, name, sd, ed, payment in periods:
        existing = await _scalar(s, """
            SELECT id FROM hr_payroll_periods WHERE organization_id = :org AND code = :code
        """, org=org_id, code=code)
        if existing:
            continue
        period_id = uuid.uuid4()
        total_gross = Decimal("0")
        total_deduct = Decimal("0")
        total_net = Decimal("0")
        emp_count = 0

        if not dry:
            await _exec(s, """
                INSERT INTO hr_payroll_periods
                  (id, organization_id, code, name, period_type, start_date, end_date,
                   payment_date, status, total_gross, total_deductions, total_net,
                   employee_count, created_at, updated_at)
                VALUES (:id, :org, :code, :name, 'monthly', :sd, :ed, :pd,
                        'paid', 0, 0, 0, 0, NOW(), NOW())
            """, id=period_id, org=org_id, code=code, name=name, sd=sd, ed=ed, pd=payment)

        for emp_code, emp_id in code_to_emp.items():
            if emp_id not in by_emp:
                continue
            base, aux = by_emp[emp_id]
            ibc = base + aux
            # Cálculo conservador
            sueldo = base
            aux_amount = aux
            salud_emp = (ibc * Decimal("0.04")).quantize(Decimal("0.01"))
            pension_emp = (ibc * Decimal("0.04")).quantize(Decimal("0.01"))
            gross = sueldo + aux_amount
            deduct = salud_emp + pension_emp
            net = gross - deduct

            payroll_id = uuid.uuid4()
            if not dry:
                # Resolver department_name / position_name del empleado
                emp_meta = await _fetch_all(s, """
                    SELECT e.first_name, e.last_name, e.employee_code,
                           d.name AS dept, p.name AS pos
                    FROM hr_employees e
                    LEFT JOIN hr_departments d ON d.id = e.department_id
                    LEFT JOIN hr_positions p ON p.id = e.position_id
                    WHERE e.id = :id
                """, id=emp_id)
                meta = emp_meta[0] if emp_meta else None
                full = " ".join([meta.first_name or "", meta.last_name or ""]).strip() if meta else emp_code
                dept_name = meta.dept if meta else None
                pos_name = meta.pos if meta else None

                await _exec(s, """
                    INSERT INTO hr_payrolls
                      (id, organization_id, period_id, employee_id, employee_code, employee_name,
                       department_name, position_name, base_salary, worked_days, absence_days,
                       total_earnings, total_deductions, total_benefits, total_employer_contrib,
                       net_amount, status, paid_at, created_at, updated_at)
                    VALUES (:id, :org, :pid, :eid, :ec, :en, :dn, :pn, :bs, 30, 0,
                            :gross, :deduct, 0, 0, :net, 'paid', :paid, NOW(), NOW())
                """, id=payroll_id, org=org_id, pid=period_id, eid=emp_id, ec=emp_code,
                  en=full, dn=dept_name, pn=pos_name, bs=base, gross=gross, deduct=deduct,
                  net=net, paid=datetime.combine(payment, datetime.min.time()))

                # 4 ítems mínimos
                items_data = [
                    ("SUELDO", "Sueldo básico", "earning", 30, None, sueldo, 10),
                    ("AUX_TRANS", "Auxilio de transporte", "earning", 1, None, aux_amount, 20),
                    ("SALUD_EMP", "Aporte salud empleado", "deduction", None, Decimal("4"), salud_emp, 100),
                    ("PENSION_EMP", "Aporte pensión empleado", "deduction", None, Decimal("4"), pension_emp, 101),
                ]
                for code_i, name_i, type_i, qty, pct, amt, so in items_data:
                    await _exec(s, """
                        INSERT INTO hr_payroll_items
                          (id, payroll_id, concept_code, concept_name, concept_type,
                           quantity, percentage, amount, sort_order, created_at)
                        VALUES (:id, :pid, :cc, :cn, :ct, :qty, :pct, :amt, :so, NOW())
                    """, id=uuid.uuid4(), pid=payroll_id, cc=code_i, cn=name_i,
                      ct=type_i, qty=qty, pct=pct, amt=amt, so=so)
                    items_created += 1

            total_gross += gross
            total_deduct += deduct
            total_net += net
            emp_count += 1
            payrolls_created += 1

        if not dry:
            await _exec(s, """
                UPDATE hr_payroll_periods SET
                  total_gross = :g, total_deductions = :d, total_net = :n,
                  employee_count = :ec, status = 'paid',
                  calculated_at = NOW(), approved_at = NOW(), paid_at = NOW()
                WHERE id = :id
            """, g=total_gross, d=total_deduct, n=total_net, ec=emp_count, id=period_id)
        periods_created += 1

    print(f"  · períodos: {periods_created} creados, {payrolls_created} payrolls, {items_created} items")


async def seed_vacations(
    s, org_id: uuid.UUID, code_to_emp: dict[str, uuid.UUID], dry: bool,
):
    """Saldos 2026 + 2 solicitudes (1 aprobada, 1 pendiente)."""
    balances_created = 0
    for emp_code, emp_id in code_to_emp.items():
        existing = await _scalar(s, """
            SELECT id FROM hr_vacation_balances WHERE employee_id = :id AND period_year = 2026
        """, id=emp_id)
        if existing:
            continue
        if not dry:
            # 15 días causados proporcionales (aprox. para enero–junio)
            await _exec(s, """
                INSERT INTO hr_vacation_balances
                  (id, organization_id, employee_id, period_year, days_accrued, days_taken,
                   days_pending, days_compensated, created_at, updated_at)
                VALUES (:id, :org, :eid, 2026, 6.25, 0, 0, 0, NOW(), NOW())
            """, id=uuid.uuid4(), org=org_id, eid=emp_id)
        balances_created += 1

    # 2 solicitudes ejemplo
    requests = [
        ("AUX-002", "VR-2026-001", date(2026, 7, 1), date(2026, 7, 7), "7.00",
         "approved", "Vacaciones familiares de mitad de año"),
        ("COND-001", "VR-2026-002", date(2026, 8, 15), date(2026, 8, 21), "7.00",
         "pending", "Solicitud para asuntos personales"),
    ]
    req_inserted = 0
    for emp_code, num, sd, ed, days, status, reason in requests:
        if emp_code not in code_to_emp:
            continue
        existing = await _scalar(s, """
            SELECT id FROM hr_vacation_requests WHERE organization_id = :org AND request_number = :n
        """, org=org_id, n=num)
        if existing:
            continue
        if not dry:
            approved_at = datetime(2026, 6, 1) if status == "approved" else None
            await _exec(s, """
                INSERT INTO hr_vacation_requests
                  (id, organization_id, employee_id, request_number, request_type,
                   start_date, end_date, days_count, status, request_reason,
                   requested_at, approved_at, created_at, updated_at)
                VALUES (:id, :org, :eid, :n, 'paid', :sd, :ed, :dc, :st, :reason,
                        :req_at, :app_at, NOW(), NOW())
            """, id=uuid.uuid4(), org=org_id, eid=code_to_emp[emp_code], n=num, sd=sd, ed=ed,
              dc=days, st=status, reason=reason,
              req_at=datetime(2026, 5, 20), app_at=approved_at)
            if status == "approved":
                # mover saldo a days_pending
                await _exec(s, """
                    UPDATE hr_vacation_balances SET days_pending = days_pending + :d, updated_at = NOW()
                    WHERE employee_id = :eid AND period_year = 2026
                """, d=Decimal(days), eid=code_to_emp[emp_code])
        req_inserted += 1
    print(f"  · vacaciones: {balances_created} saldos, {req_inserted} solicitudes")


async def seed_leaves(s, org_id: uuid.UUID, code_to_emp: dict[str, uuid.UUID], dry: bool):
    leaves = [
        ("AUX-003", "LV-2026-001", "medical", "incapacidad general", date(2026, 5, 28), date(2026, 6, 4),
         "8", True, "66.67", "active", "EPS Sura", "INC-441223", "J32.9"),
        ("COND-002", "LV-2026-002", "paternity", None, date(2026, 3, 1), date(2026, 3, 14),
         "14", True, "100.00", "completed", "EPS Sanitas", "PAT-09221", None),
    ]
    inserted = 0
    for emp_code, num, ltype, subtype, sd, ed, days, paid, pct, status, issuer, doc, dx in leaves:
        if emp_code not in code_to_emp:
            continue
        existing = await _scalar(s, """
            SELECT id FROM hr_leaves WHERE organization_id = :org AND leave_number = :n
        """, org=org_id, n=num)
        if existing:
            continue
        if not dry:
            await _exec(s, """
                INSERT INTO hr_leaves
                  (id, organization_id, employee_id, leave_number, leave_type, subtype,
                   start_date, end_date, days_count, is_paid, paid_percentage, status,
                   supporting_doc_issuer, supporting_doc_number, diagnosis_code, created_at, updated_at)
                VALUES (:id, :org, :eid, :n, :lt, :st_, :sd, :ed, :dc, :paid, :pct, :status,
                        :issuer, :doc, :dx, NOW(), NOW())
            """, id=uuid.uuid4(), org=org_id, eid=code_to_emp[emp_code], n=num,
              lt=ltype, st_=subtype, sd=sd, ed=ed, dc=Decimal(days), paid=paid,
              pct=Decimal(pct), status=status, issuer=issuer, doc=doc, dx=dx)
        inserted += 1
    print(f"  · incapacidades/licencias: {inserted}")


async def seed_evaluations(s, org_id: uuid.UUID, code_to_emp: dict[str, uuid.UUID], dry: bool):
    """1 ciclo abierto + evaluación auto por empleado (algunas completadas)."""
    cycle_code = "EVAL-2026-1"
    existing = await _scalar(s, """
        SELECT id FROM hr_evaluation_cycles WHERE organization_id = :org AND code = :c
    """, org=org_id, c=cycle_code)
    if existing:
        cycle_id = existing
    else:
        cycle_id = uuid.uuid4()
        if not dry:
            await _exec(s, """
                INSERT INTO hr_evaluation_cycles
                  (id, organization_id, code, name, description, period_label, start_date, end_date,
                   enable_self, enable_supervisor, enable_360, scale_min, scale_max, competencies,
                   status, opened_at, created_at, updated_at)
                VALUES (:id, :org, :code, :name, :desc, :pl, :sd, :ed, true, true, false,
                        1, 5, CAST(:comp AS JSONB), 'open', NOW(), NOW(), NOW())
            """, id=cycle_id, org=org_id, code=cycle_code,
              name="Evaluación semestral 2026-1",
              desc="Evaluación de desempeño primer semestre de 2026",
              pl="2026-S1", sd=date(2026, 6, 1), ed=date(2026, 6, 30),
              comp=json.dumps(COMPETENCIES))

    # 1 evaluación por empleado, con 4 completadas (auto+jefe) y 4 en progreso
    completados = ["DIR-001", "COORD-001", "COORD-002", "AUX-001"]
    inserted = 0
    for emp_code, emp_id in code_to_emp.items():
        existing_eval = await _scalar(s, """
            SELECT id FROM hr_evaluations WHERE cycle_id = :c AND employee_id = :e
        """, c=cycle_id, e=emp_id)
        if existing_eval:
            continue
        eval_id = uuid.uuid4()
        full_complete = emp_code in completados
        score = Decimal("4.35") if full_complete else None
        status = "completed" if full_complete else "in_progress"
        if not dry:
            await _exec(s, """
                INSERT INTO hr_evaluations
                  (id, organization_id, cycle_id, employee_id, self_completed,
                   supervisor_completed, overall_score, status, completed_at,
                   created_at, updated_at)
                VALUES (:id, :org, :c, :e, :sc, :su, :ov, :st, :cp, NOW(), NOW())
            """, id=eval_id, org=org_id, c=cycle_id, e=emp_id,
              sc=full_complete, su=full_complete, ov=score, st=status,
              cp=datetime(2026, 6, 15) if full_complete else None)

            if full_complete:
                # auto + supervisor responses
                for etype in ("self", "supervisor"):
                    scores = {comp["code"]: 4.0 + (0.5 if etype == "supervisor" else 0)
                              for comp in COMPETENCIES}
                    overall = sum(scores[c["code"]] * (c["weight"] / 100) for c in COMPETENCIES)
                    await _exec(s, """
                        INSERT INTO hr_evaluation_responses
                          (id, organization_id, evaluation_id, evaluator_type, scores,
                           overall_score, comments, submitted_at, created_at)
                        VALUES (:id, :org, :ev, :et, CAST(:sc AS JSONB), :ov,
                                :comm, NOW(), NOW())
                    """, id=uuid.uuid4(), org=org_id, ev=eval_id, et=etype,
                      sc=json.dumps(scores), ov=overall,
                      comm="Buen desempeño en general." if etype == "supervisor" else "Me siento conforme con mi trabajo.")
        inserted += 1
    print(f"  · evaluaciones: ciclo + {inserted} empleados")


async def seed_training(s, org_id: uuid.UUID, code_to_emp: dict[str, uuid.UUID], dry: bool):
    course_ids: dict[str, uuid.UUID] = {}
    for code, name, desc, cat, hours, mode, mandatory, provider in COURSES:
        existing = await _scalar(s, """
            SELECT id FROM hr_training_courses WHERE organization_id = :org AND code = :c
        """, org=org_id, c=code)
        if existing:
            course_ids[code] = existing
            continue
        new_id = uuid.uuid4()
        course_ids[code] = new_id
        if not dry:
            await _exec(s, """
                INSERT INTO hr_training_courses
                  (id, organization_id, code, name, description, category, duration_hours,
                   delivery_mode, is_mandatory, provider, is_active, created_at, updated_at)
                VALUES (:id, :org, :code, :name, :desc, :cat, :hrs, :mode, :mand, :prov,
                        true, NOW(), NOW())
            """, id=new_id, org=org_id, code=code, name=name, desc=desc, cat=cat,
              hrs=Decimal(hours), mode=mode, mand=mandatory, prov=provider)

    # Matrículas: BIO-2026 → todos los OPS, ATFAM-01 → AUX/COORD, SST-2026 → todos
    enrollments_plan = [
        ("BIO-2026", ["AUX-001", "AUX-002", "AUX-003", "COND-001", "COND-002"], "completed"),
        ("ATFAM-01", ["AUX-001", "AUX-002", "COORD-001"], "in_progress"),
        ("SST-2026", list(code_to_emp.keys()), "enrolled"),
    ]
    enrolled = 0
    for course_code, emp_codes, default_status in enrollments_plan:
        if course_code not in course_ids:
            continue
        cid = course_ids[course_code]
        for ec in emp_codes:
            if ec not in code_to_emp:
                continue
            existing = await _scalar(s, """
                SELECT id FROM hr_training_enrollments
                WHERE course_id = :c AND employee_id = :e
            """, c=cid, e=code_to_emp[ec])
            if existing:
                continue
            completed = default_status == "completed"
            score = Decimal("4.5") if completed else None
            if not dry:
                await _exec(s, """
                    INSERT INTO hr_training_enrollments
                      (id, organization_id, course_id, employee_id, scheduled_date,
                       completed_date, completion_status, score, attendance_pct,
                       created_at, updated_at)
                    VALUES (:id, :org, :c, :e, :sd, :cd, :status, :score, :att,
                            NOW(), NOW())
                """, id=uuid.uuid4(), org=org_id, c=cid, e=code_to_emp[ec],
                  sd=date(2026, 4, 1), cd=date(2026, 5, 15) if completed else None,
                  status=default_status, score=score,
                  att=Decimal("100") if completed else None)
            enrolled += 1
    print(f"  · capacitaciones: {len(course_ids)} cursos, {enrolled} matrículas")


async def seed_documents(s, org_id: uuid.UUID, code_to_emp: dict[str, uuid.UUID], dry: bool):
    doc_templates = [
        ("resume", "Hoja de vida actualizada"),
        ("contract", "Contrato laboral firmado"),
        ("eps_affiliation", "Afiliación EPS"),
        ("pension_affiliation", "Afiliación pensión"),
        ("arl_affiliation", "Afiliación ARL"),
    ]
    inserted = 0
    for emp_code, emp_id in code_to_emp.items():
        for dtype, title in doc_templates:
            existing = await _scalar(s, """
                SELECT id FROM hr_employee_documents
                WHERE employee_id = :e AND document_type = :t
            """, e=emp_id, t=dtype)
            if existing:
                continue
            if not dry:
                await _exec(s, """
                    INSERT INTO hr_employee_documents
                      (id, organization_id, employee_id, document_type, title,
                       issue_date, status, created_at, updated_at)
                    VALUES (:id, :org, :eid, :dt, :title, :issue, 'valid', NOW(), NOW())
                """, id=uuid.uuid4(), org=org_id, eid=emp_id, dt=dtype, title=title,
                  issue=date(2026, 1, 15))
            inserted += 1
    print(f"  · documentos: {inserted}")


# ============================================================ Main


async def seed(dry: bool):
    async with async_session_factory() as session:
        async with session.begin():
            conn = await session.connection()
            org = await _scalar(conn, """
                SELECT id FROM organizations WHERE slug = :slug
            """, slug=ORG_SLUG)
            if not org:
                print(f"❌ Organización con slug '{ORG_SLUG}' no encontrada.")
                return
            print(f"▶ Seed San Rafael en org {org} (dry={dry})\n")

            await seed_org_settings(conn, org, dry)
            depts = await seed_departments(conn, org, dry)
            shifts = await seed_shifts(conn, org, dry)
            code_to_emp = await assign_employees_to_dept_and_supervisor(conn, org, depts, dry)
            await seed_concepts(conn, org, dry)
            await seed_payroll_periods_and_runs(conn, org, code_to_emp, dry)
            await seed_vacations(conn, org, code_to_emp, dry)
            await seed_leaves(conn, org, code_to_emp, dry)
            await seed_evaluations(conn, org, code_to_emp, dry)
            await seed_training(conn, org, code_to_emp, dry)
            await seed_documents(conn, org, code_to_emp, dry)

            if dry:
                await session.rollback()
                print("\nDRY-RUN — nada persistido.")
            else:
                print("\n✓ Seed San Rafael completo.")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed HR Funeraria San Rafael")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        asyncio.run(seed(args.dry_run))
    finally:
        asyncio.run(engine.dispose())


if __name__ == "__main__":
    main()
