"""Plantillas de automatización: flujos prearmados que el usuario instala con un clic."""

from __future__ import annotations

from typing import Any

TEMPLATES: list[dict[str, Any]] = [
    {
        "key": "low_stock_alert",
        "name": "Avísame del stock bajo",
        "description": "Cuando un producto llega al mínimo, crea una notificación.",
        "icon": "📦",
        "trigger_type": "pos_low_stock",
        "trigger_config": {},
        "steps": [
            {"kind": "action", "type": "notify", "config": {
                "title": "{count} producto(s) en stock bajo",
                "body": "Revisa Sugerencias IA para el reorden recomendado.",
                "level": "warning", "link": "/pos/insights"}},
        ],
    },
    {
        "key": "high_risk_customers",
        "name": "Clientes en mora alta",
        "description": "Detecta clientes con cartera muy vencida y crea una alerta para llamarlos.",
        "icon": "⚠️",
        "trigger_type": "memorial_overdue",
        "trigger_config": {},
        "steps": [
            {"kind": "condition", "type": "field_compare",
             "config": {"field": "risk_tier", "op": "eq", "value": "alto"}},
            {"kind": "action", "type": "notify", "config": {
                "title": "{count} cliente(s) en riesgo ALTO de cartera",
                "body": "Llámalos hoy. Ver Riesgo de cartera para los detalles.",
                "level": "danger", "link": "/memorial/risk"}},
        ],
    },
    {
        "key": "daily_summary",
        "name": "Resumen del día",
        "description": "Cada día crea una notificación con el resumen del negocio.",
        "icon": "🗓️",
        "trigger_type": "schedule_daily",
        "trigger_config": {"time": "08:00"},
        "steps": [
            {"kind": "action", "type": "notify", "config": {
                "title": "Tu resumen del día está listo",
                "body": "Abre el inicio para ver el resumen completo.",
                "level": "info", "link": "/dashboard"}},
        ],
    },
]


def get_template(key: str) -> dict[str, Any] | None:
    return next((t for t in TEMPLATES if t["key"] == key), None)
