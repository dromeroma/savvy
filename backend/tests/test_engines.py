"""Tests unitarios de los motores de dinero y seguridad de fórmulas. Sin BD.

Estos son los que protegen la plata: nómina, liquidación, costo de IA, y el
evaluador de fórmulas (que NO debe permitir código arbitrario).
"""

from datetime import date
from decimal import Decimal

import pytest

from src.apps.hr.liquidation_engine import calculate_liquidation
from src.apps.hr.payroll_engine import _safe_eval
from src.modules.savvy_ai.pricing import compute_cost


# ============================================================ Evaluador de fórmulas

def test_safe_eval_arithmetic():
    env = {"salario": Decimal("1000000"), "dias": Decimal("30")}
    assert _safe_eval("salario * 0.04", env) == Decimal("40000.00")
    assert _safe_eval("salario / dias", env) == Decimal("33333.333333333333333333333333")
    assert _safe_eval("max(salario, 500000)", env) == Decimal("1000000")
    assert _safe_eval("round(salario * 0.0833, 0)", env) == Decimal("83300")


@pytest.mark.parametrize("evil", [
    "__import__('os').system('rm -rf /')",
    "salario.__class__",
    "open('/etc/passwd')",
    "().__class__.__bases__",
    "desconocida + 1",          # variable no en env
    "exec('x=1')",
])
def test_safe_eval_rejects_malicious(evil):
    with pytest.raises((ValueError, Exception)):
        _safe_eval(evil, {"salario": Decimal("1000000")})


# ============================================================ Liquidación (ley 50)

def _liq(**kw):
    base = dict(
        contract_start_date=date(2023, 1, 16),
        termination_date=date(2026, 6, 15),
        last_worked_date=date(2026, 6, 15),
        termination_reason="voluntary",
        base_salary=Decimal("2000000"),
        transport_allowance=Decimal("162000"),
    )
    base.update(kw)
    return calculate_liquidation(**base)


def test_liquidation_totals_consistent():
    r = _liq()
    earnings = sum((i.amount for i in r.items if i.kind == "earning"), Decimal("0"))
    deductions = sum((i.amount for i in r.items if i.kind == "deduction"), Decimal("0"))
    assert r.total_earnings == earnings
    assert r.total_deductions == deductions
    assert r.net_amount == earnings - deductions


def test_liquidation_has_core_concepts():
    r = _liq()
    codes = {i.code for i in r.items}
    assert "cesantias" in codes
    assert "intereses_cesantias" in codes
    assert "prima_servicios" in codes


def test_liquidation_indemnizacion_only_without_cause():
    voluntary = {i.code for i in _liq(termination_reason="voluntary").items}
    assert "indemnizacion_sin_causa" not in voluntary
    without = {i.code for i in _liq(termination_reason="without_cause").items}
    assert "indemnizacion_sin_causa" in without


def test_liquidation_legal_protection_blocks_indemnizacion():
    r = _liq(termination_reason="without_cause", has_legal_protection=True)
    assert "indemnizacion_sin_causa" not in {i.code for i in r.items}


def test_liquidation_ibc_includes_transport():
    r = _liq()
    # average_salary (IBC) = base + auxilio de transporte
    assert r.average_salary == Decimal("2162000")


# ============================================================ Costo de IA

def test_compute_cost_known_model():
    # Sonnet: 3 USD/1M input, 15 USD/1M output.
    cost = compute_cost("claude-sonnet-4-6", 1_000_000, 1_000_000)
    assert cost == Decimal("18.000000")


def test_compute_cost_unknown_model_is_zero():
    assert compute_cost("modelo-inexistente", 1000, 1000) == Decimal("0")


def test_compute_cost_cached_cheaper():
    full = compute_cost("claude-sonnet-4-6", 1_000_000, 0)
    cached = compute_cost("claude-sonnet-4-6", 0, 0, cached_tokens=1_000_000)
    assert cached < full
