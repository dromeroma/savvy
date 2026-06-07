"""Motor de cálculo de liquidación laboral (Colombia, ley 50).

Calcula automáticamente los conceptos de la liquidación final al
terminar el contrato. RRHH puede luego editar/agregar ítems manuales.

Conceptos auto-calculados:
  - Días pendientes del último período
  - Cesantías (8.33% × días_totales_año / 360)
  - Intereses cesantías (12% × cesantías × días_año / 360)
  - Prima de servicios (8.33% × días_semestre / 180)
  - Vacaciones compensadas (4.17% × días_totales / 720)
  - Indemnización por despido (si terminación sin justa causa)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def _round(value: Decimal | float | int) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _days_between(start: date, end: date) -> int:
    if end < start:
        return 0
    return (end - start).days + 1


def _year_days(start: date, end: date) -> int:
    """Días corridos para fórmulas prestacionales (360 días año)."""
    return _days_between(start, end)


@dataclass
class LiquidationLine:
    code: str
    name: str
    kind: str  # 'earning' | 'deduction'
    quantity: Decimal
    base_amount: Decimal
    rate: Decimal | None
    amount: Decimal
    sort_order: int
    notes: str | None = None


@dataclass
class LiquidationResult:
    base_salary: Decimal
    average_salary: Decimal
    days_worked_total: int
    contract_start_date: date
    last_worked_date: date
    termination_date: date
    termination_reason: str
    total_earnings: Decimal
    total_deductions: Decimal
    net_amount: Decimal
    items: list[LiquidationLine] = field(default_factory=list)


def calculate_liquidation(
    *,
    contract_start_date: date,
    termination_date: date,
    last_worked_date: date,
    termination_reason: str,
    base_salary: Decimal,
    transport_allowance: Decimal = Decimal("0"),
    has_legal_protection: bool = False,
    pending_period_days: int = 0,
    vacation_days_pending: Decimal = Decimal("0"),
    extra_earnings: list[tuple[str, str, Decimal]] | None = None,
    extra_deductions: list[tuple[str, str, Decimal]] | None = None,
) -> LiquidationResult:
    """Calcula la liquidación. Devuelve líneas + totales.

    Args:
        contract_start_date: Fecha de inicio del contrato.
        termination_date: Fecha de terminación legal.
        last_worked_date: Último día laborado (puede ser anterior si hubo aviso).
        termination_reason: voluntary|mutual|with_cause|without_cause|end_of_contract|...
        base_salary: Salario mensual base.
        transport_allowance: Auxilio de transporte.
        has_legal_protection: Fuero (sindical/maternal). Si True, no se aplica
                              terminación sin justa causa unilateral.
        pending_period_days: Días del último período no liquidados aún.
        vacation_days_pending: Días de vacaciones causadas no disfrutadas.
        extra_earnings: Lista de (code, name, amount) adicionales auto.
        extra_deductions: Lista de (code, name, amount) adicionales auto.
    """
    base = _round(base_salary)
    aux = _round(transport_allowance)
    daily_salary = _round(base / Decimal("30"))
    # IBC para prestaciones: salario + auxilio de transporte
    ibc = base + aux

    days_total = _year_days(contract_start_date, last_worked_date)
    items: list[LiquidationLine] = []

    # 1) Días pendientes del último período
    if pending_period_days > 0:
        pending_amount = _round(daily_salary * Decimal(pending_period_days))
        items.append(LiquidationLine(
            code="salario_pendiente",
            name=f"Salario pendiente ({pending_period_days} días)",
            kind="earning", quantity=Decimal(pending_period_days),
            base_amount=daily_salary, rate=None,
            amount=pending_amount, sort_order=1,
        ))

    # 2) Cesantías = IBC × días_año / 360
    cesantias = _round(ibc * Decimal(days_total) / Decimal("360"))
    items.append(LiquidationLine(
        code="cesantias", name="Cesantías",
        kind="earning", quantity=Decimal(days_total),
        base_amount=ibc, rate=Decimal("0.0833"),
        amount=cesantias, sort_order=10,
        notes=f"{days_total} días sobre IBC ${ibc:,.2f}",
    ))

    # 3) Intereses cesantías = cesantías × 12% × días_año / 360
    intereses = _round(cesantias * Decimal("0.12") * Decimal(days_total) / Decimal("360"))
    items.append(LiquidationLine(
        code="intereses_cesantias", name="Intereses sobre cesantías (12%)",
        kind="earning", quantity=Decimal(days_total),
        base_amount=cesantias, rate=Decimal("0.12"),
        amount=intereses, sort_order=11,
    ))

    # 4) Prima de servicios = IBC × días_semestre / 180
    # Se calcula sobre el último semestre. Para simplificar tomamos
    # min(días_año, 180) como aproximación. RRHH puede ajustar.
    prima_days = min(days_total, 180)
    prima = _round(ibc * Decimal(prima_days) / Decimal("360"))
    items.append(LiquidationLine(
        code="prima_servicios", name="Prima de servicios",
        kind="earning", quantity=Decimal(prima_days),
        base_amount=ibc, rate=Decimal("0.0833"),
        amount=prima, sort_order=12,
        notes=f"{prima_days} días del último semestre",
    ))

    # 5) Vacaciones compensadas
    if vacation_days_pending > 0:
        vac_amount = _round(daily_salary * vacation_days_pending)
        items.append(LiquidationLine(
            code="vacaciones_compensadas", name="Vacaciones compensadas en dinero",
            kind="earning", quantity=vacation_days_pending,
            base_amount=daily_salary, rate=None,
            amount=vac_amount, sort_order=13,
        ))
    else:
        # Auto-cálculo: 1 día por cada 20 días trabajados aprox (4.17%)
        vac_days_calc = _round(Decimal(days_total) / Decimal("20"))
        vac_amount = _round(daily_salary * vac_days_calc)
        items.append(LiquidationLine(
            code="vacaciones_proporcionales", name="Vacaciones proporcionales",
            kind="earning", quantity=vac_days_calc,
            base_amount=daily_salary, rate=Decimal("0.0417"),
            amount=vac_amount, sort_order=13,
            notes="Estimado 1 día por cada 20 días trabajados",
        ))

    # 6) Indemnización por despido sin justa causa (Ley 50)
    if termination_reason == "without_cause" and not has_legal_protection:
        # Salarios ≤ 10 SMLMV: 30 días + 20 días por año adicional al primero
        # Salarios > 10 SMLMV: 20 días + 15 días por año adicional al primero
        smlmv_2026 = Decimal("1500000")  # placeholder configurable
        per_year_threshold = ibc / smlmv_2026
        years = Decimal(days_total) / Decimal("365")

        if per_year_threshold <= 10:
            base_days = 30
            extra_per_year = 20
        else:
            base_days = 20
            extra_per_year = 15

        if years <= 1:
            indemn_days = Decimal(base_days)
        else:
            extra_years = years - 1
            indemn_days = Decimal(base_days) + Decimal(extra_per_year) * extra_years

        indemn_days = _round(indemn_days)
        indemn_amount = _round(daily_salary * indemn_days)
        items.append(LiquidationLine(
            code="indemnizacion_sin_causa",
            name="Indemnización por despido sin justa causa (Ley 50)",
            kind="earning", quantity=indemn_days,
            base_amount=daily_salary, rate=None,
            amount=indemn_amount, sort_order=20,
            notes=f"{base_days} días base + {extra_per_year}×({years:.2f}-1) años extra",
        ))

    # Extras opcionales
    if extra_earnings:
        for i, (code, name, amt) in enumerate(extra_earnings):
            items.append(LiquidationLine(
                code=code, name=name, kind="earning",
                quantity=Decimal("1"), base_amount=Decimal("0"),
                rate=None, amount=_round(amt), sort_order=30 + i,
            ))

    # Deducciones: retención en la fuente sobre ingresos no laborales (simplificado: 0 por defecto)
    # RRHH puede agregar manualmente.
    if extra_deductions:
        for i, (code, name, amt) in enumerate(extra_deductions):
            items.append(LiquidationLine(
                code=code, name=name, kind="deduction",
                quantity=Decimal("1"), base_amount=Decimal("0"),
                rate=None, amount=_round(amt), sort_order=50 + i,
            ))

    total_earnings = _round(sum(
        (it.amount for it in items if it.kind == "earning"),
        start=Decimal("0"),
    ))
    total_deductions = _round(sum(
        (it.amount for it in items if it.kind == "deduction"),
        start=Decimal("0"),
    ))
    net = _round(total_earnings - total_deductions)

    return LiquidationResult(
        base_salary=base,
        average_salary=ibc,
        days_worked_total=days_total,
        contract_start_date=contract_start_date,
        last_worked_date=last_worked_date,
        termination_date=termination_date,
        termination_reason=termination_reason,
        total_earnings=total_earnings,
        total_deductions=total_deductions,
        net_amount=net,
        items=items,
    )
