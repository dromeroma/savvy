"""Tests unitarios de la lógica pura de SavvyFlow y Savvy Graph. Sin BD."""

from src.modules.savvy_ai.graph import _strip_accents
from src.modules.savvy_flow.engine import _apply_condition, _render


# ============================================================ Graph (acentos)

def test_strip_accents():
    assert _strip_accents("Cárdenas") == "cardenas"
    assert _strip_accents("MUÑOZ") == "munoz"
    assert _strip_accents("José Pérez") == "jose perez"
    assert _strip_accents("Ñoño") == "nono"


# ============================================================ Flow: condiciones

def _items():
    return [
        {"name": "A", "risk_tier": "alto", "days_late": 120},
        {"name": "B", "risk_tier": "medio", "days_late": 40},
        {"name": "C", "risk_tier": "alto", "days_late": 95},
        {"name": "D", "risk_tier": "bajo", "days_late": 5},
    ]


def test_condition_eq():
    out = _apply_condition(_items(), {"field": "risk_tier", "op": "eq", "value": "alto"})
    assert {i["name"] for i in out} == {"A", "C"}


def test_condition_gt():
    out = _apply_condition(_items(), {"field": "days_late", "op": "gt", "value": "90"})
    assert {i["name"] for i in out} == {"A", "C"}


def test_condition_lte():
    out = _apply_condition(_items(), {"field": "days_late", "op": "lte", "value": "40"})
    assert {i["name"] for i in out} == {"B", "D"}


def test_condition_contains():
    out = _apply_condition(_items(), {"field": "risk_tier", "op": "contains", "value": "med"})
    assert {i["name"] for i in out} == {"B"}


def test_condition_missing_field_is_noop():
    items = _items()
    assert _apply_condition(items, {"op": "eq", "value": "x"}) == items


# ============================================================ Flow: templates

def test_render_replaces_vars():
    assert _render("{count} clientes", {"count": 15}) == "15 clientes"
    assert _render("sin variables", {"count": 1}) == "sin variables"
    assert _render("{a} y {b}", {"a": "uno", "b": "dos"}) == "uno y dos"
