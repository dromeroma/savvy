"""SavvyHR · motor de cálculo de nómina.

Evalúa conceptos en orden según `sort_order`. Tres métodos:

  - fixed             → usa concept.fixed_value
  - percentage        → concept.percentage_value × base_amount
                        (base_amount = base_concept_code ya calculado, o base_salary)
  - formula           → expresión segura con variables: base_salary, worked_days,
                        overtime_day, overtime_night, transport_allowance,
                        food_allowance, connectivity_allowance, other_allowance,
                        plus any concept_code previamente calculado.
  - quantity_rate     → quantity × rate (toma quantity/rate de inputs externos)

Todos los conceptos se acumulan en `computed[concept_code] = amount` para que
los siguientes puedan referenciarlos como base.

Salida: lista de items (concept × amount) + totales por tipo.
"""

from __future__ import annotations

import ast
import operator
import uuid
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hr.models import (
    HrAttendance,
    HrContract,
    HrEmployee,
    HrPayrollConcept,
)


_ALLOWED_OPS: dict[type[ast.AST], Any] = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def _safe_eval(expr: str, env: dict[str, Decimal]) -> Decimal:
    """Evalúa una expresión aritmética simple con identificadores en env.

    Solo permite: literales numéricos, identificadores en `env`, + - * / %,
    paréntesis y funciones `min`, `max`, `round`. Nada de atributos/llamadas
    arbitrarias.
    """
    tree = ast.parse(expr, mode="eval")
    allowed_funcs = {"min": min, "max": max, "round": round}

    def _eval(node: ast.AST) -> Decimal:
        if isinstance(node, ast.Expression):
            return _eval(node.body)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return Decimal(str(node.value))
            raise ValueError(f"constante no permitida: {node.value!r}")
        if isinstance(node, ast.Name):
            if node.id not in env:
                raise ValueError(f"variable desconocida: {node.id}")
            return Decimal(str(env[node.id]))
        if isinstance(node, ast.BinOp):
            op = _ALLOWED_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"operador no permitido: {type(node.op).__name__}")
            return Decimal(str(op(_eval(node.left), _eval(node.right))))
        if isinstance(node, ast.UnaryOp):
            op = _ALLOWED_OPS.get(type(node.op))
            if op is None:
                raise ValueError(f"operador unario no permitido")
            return Decimal(str(op(_eval(node.operand))))
        if isinstance(node, ast.Call):
            if not isinstance(node.func, ast.Name) or node.func.id not in allowed_funcs:
                raise ValueError("función no permitida")
            args = [_eval(a) for a in node.args]
            return Decimal(str(allowed_funcs[node.func.id](*args)))
        raise ValueError(f"nodo no permitido: {type(node).__name__}")

    return _eval(tree)


@dataclass
class PayrollItemData:
    concept_id: uuid.UUID | None
    concept_code: str
    concept_name: str
    concept_type: str
    category: str
    quantity: Decimal | None = None
    rate: Decimal | None = None
    base_amount: Decimal | None = None
    percentage: Decimal | None = None
    amount: Decimal = Decimal("0")
    sort_order: int = 100


@dataclass
class PayrollCalculation:
    employee_id: uuid.UUID
    employee_code: str
    employee_name: str
    department_name: str | None
    position_name: str | None
    contract_id: uuid.UUID | None
    base_salary: Decimal
    worked_days: Decimal
    absence_days: Decimal
    total_earnings: Decimal = Decimal("0")
    total_deductions: Decimal = Decimal("0")
    total_benefits: Decimal = Decimal("0")
    total_employer_contrib: Decimal = Decimal("0")
    net_amount: Decimal = Decimal("0")
    items: list[PayrollItemData] = field(default_factory=list)


async def calculate_employee_payroll(
    db: AsyncSession,
    org_id: uuid.UUID,
    employee: HrEmployee,
    contract: HrContract | None,
    period_start: date,
    period_end: date,
    concepts: list[HrPayrollConcept],
    *,
    worked_days: Decimal | None = None,
    absences: Decimal = Decimal("0"),
) -> PayrollCalculation:
    """Liquida UN empleado en el período dado.

    `worked_days` por defecto = días del período - absences.
    """
    base_salary = Decimal(contract.base_salary) if contract else Decimal("0")
    period_days = Decimal((period_end - period_start).days + 1)
    if worked_days is None:
        # Para nómina mensual estándar Colombia, 30 días
        if (period_end - period_start).days >= 27:
            worked_days = Decimal("30") - absences
        else:
            worked_days = period_days - absences

    # Recolectar asistencia del período: horas extra y novedades
    att_rows = await db.execute(
        select(HrAttendance).where(
            HrAttendance.organization_id == org_id,
            HrAttendance.employee_id == employee.id,
            HrAttendance.work_date >= period_start,
            HrAttendance.work_date <= period_end,
        )
    )
    ot_day = Decimal("0")
    ot_night = Decimal("0")
    ot_holiday = Decimal("0")
    for a in att_rows.scalars().all():
        ot_day += Decimal(a.overtime_day_hours or 0)
        ot_night += Decimal(a.overtime_night_hours or 0)
        ot_holiday += Decimal(a.overtime_holiday_hours or 0)

    # Variables para fórmulas
    transport = Decimal(contract.transport_allowance) if contract else Decimal("0")
    food = Decimal(contract.food_allowance) if contract else Decimal("0")
    connectivity = Decimal(contract.connectivity_allowance) if contract else Decimal("0")
    other_allowance = Decimal(contract.other_allowance) if contract else Decimal("0")

    # Salario hora (asumiendo 240 horas mes — 30 días × 8h)
    hourly_rate = base_salary / Decimal("240") if base_salary > 0 else Decimal("0")

    # Daily proporcional (base × días_trabajados / 30)
    daily_base = (base_salary / Decimal("30")) * worked_days if base_salary > 0 else Decimal("0")

    env: dict[str, Decimal] = {
        "base_salary": base_salary,
        "daily_base": daily_base,
        "worked_days": worked_days,
        "absence_days": absences,
        "hourly_rate": hourly_rate,
        "overtime_day": ot_day,
        "overtime_night": ot_night,
        "overtime_holiday": ot_holiday,
        "transport_allowance": transport,
        "food_allowance": food,
        "connectivity_allowance": connectivity,
        "other_allowance": other_allowance,
    }

    items: list[PayrollItemData] = []
    earnings = Decimal("0")
    deductions = Decimal("0")
    benefits = Decimal("0")
    employer = Decimal("0")
    sort_seq = 100

    # Ordenar conceptos: primero por sort_order, después por tipo (earnings antes que deductions)
    type_order = {
        "earning": 1, "informative": 2, "deduction": 3, "benefit": 4, "employer_contribution": 5,
    }
    ordered = sorted(
        concepts, key=lambda c: (type_order.get(c.concept_type, 99), c.sort_order, c.code),
    )

    for c in ordered:
        amount = Decimal("0")
        base_amount: Decimal | None = None
        percentage: Decimal | None = None

        if c.calculation_method == "fixed":
            amount = Decimal(c.fixed_value or 0)
        elif c.calculation_method == "percentage":
            percentage = Decimal(c.percentage_value or 0)
            if c.base_concept_code and c.base_concept_code in env:
                base_amount = env[c.base_concept_code]
            else:
                base_amount = daily_base if base_salary > 0 else base_salary
            amount = (base_amount * percentage / Decimal("100")).quantize(Decimal("0.01"))
        elif c.calculation_method == "formula":
            if c.formula:
                try:
                    amount = _safe_eval(c.formula, env).quantize(Decimal("0.01"))
                except Exception:
                    amount = Decimal("0")
        elif c.calculation_method == "quantity_rate":
            # Default: usa horas extra como quantity si el code lo sugiere
            if "extra_diurna" in c.code.lower() or "ot_day" in c.code.lower():
                qty = ot_day
                rate = hourly_rate * Decimal("1.25")
            elif "extra_nocturna" in c.code.lower() or "ot_night" in c.code.lower():
                qty = ot_night
                rate = hourly_rate * Decimal("1.75")
            elif "dominical" in c.code.lower() or "festivo" in c.code.lower():
                qty = ot_holiday
                rate = hourly_rate * Decimal("2.0")
            else:
                qty = Decimal("0")
                rate = Decimal("0")
            amount = (qty * rate).quantize(Decimal("0.01"))
            items.append(PayrollItemData(
                concept_id=c.id, concept_code=c.code, concept_name=c.name,
                concept_type=c.concept_type, category=c.category,
                quantity=qty, rate=rate, amount=amount, sort_order=sort_seq,
            ))
            sort_seq += 1
            env[c.code] = amount
            if c.concept_type == "earning":
                earnings += amount
            elif c.concept_type == "deduction":
                deductions += amount
            elif c.concept_type == "benefit":
                benefits += amount
            elif c.concept_type == "employer_contribution":
                employer += amount
            continue

        if amount == 0 and c.calculation_method != "fixed":
            # Saltar conceptos que dieron cero salvo que sean fijos a cero intencionales
            env[c.code] = amount
            continue

        items.append(PayrollItemData(
            concept_id=c.id, concept_code=c.code, concept_name=c.name,
            concept_type=c.concept_type, category=c.category,
            base_amount=base_amount, percentage=percentage,
            amount=amount, sort_order=sort_seq,
        ))
        sort_seq += 1
        env[c.code] = amount

        if c.concept_type == "earning":
            earnings += amount
        elif c.concept_type == "deduction":
            deductions += amount
        elif c.concept_type == "benefit":
            benefits += amount
        elif c.concept_type == "employer_contribution":
            employer += amount

    net = earnings - deductions

    # Nombre depto/cargo snapshot
    from src.apps.hr.models import HrDepartment, HrPosition
    dept_name: str | None = None
    pos_name: str | None = None
    if employee.department_id:
        d = await db.scalar(select(HrDepartment).where(HrDepartment.id == employee.department_id))
        if d:
            dept_name = d.name
    if employee.position_id:
        p = await db.scalar(select(HrPosition).where(HrPosition.id == employee.position_id))
        if p:
            pos_name = p.name

    return PayrollCalculation(
        employee_id=employee.id,
        employee_code=employee.employee_code,
        employee_name=f"{employee.first_name} {employee.last_name or ''}".strip(),
        department_name=dept_name,
        position_name=pos_name,
        contract_id=contract.id if contract else None,
        base_salary=base_salary,
        worked_days=worked_days,
        absence_days=absences,
        total_earnings=earnings,
        total_deductions=deductions,
        total_benefits=benefits,
        total_employer_contrib=employer,
        net_amount=net,
        items=items,
    )
