"""Motor de ejecución de SavvyFlow.

Un flujo = trigger → (condiciones)* → (acciones)*. El trigger produce una lista
de "items"; las condiciones la filtran; las acciones se ejecutan sobre el
resultado. Todo queda registrado en automation_runs.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.savvy_flow.models import (
    AutomationNotification,
    AutomationRun,
    AutomationStep,
    AutomationWorkflow,
)


def _now() -> datetime:
    return datetime.now(UTC)


# ============================================================ Catálogo (para la UI)

TRIGGERS: list[dict[str, Any]] = [
    {"type": "manual", "label": "Manual", "icon": "▶️",
     "desc": "Se ejecuta solo cuando le das al botón.", "config_fields": []},
    {"type": "schedule_daily", "label": "Cada día", "icon": "🗓️",
     "desc": "Se ejecuta una vez al día (al evaluar automatizaciones).",
     "config_fields": [{"key": "time", "label": "Hora", "type": "time", "default": "08:00"}]},
    {"type": "pos_low_stock", "label": "Stock bajo (POS)", "icon": "📦",
     "desc": "Cuando uno o más productos llegan al stock mínimo.", "config_fields": []},
    {"type": "memorial_overdue", "label": "Cartera vencida (Memorial)", "icon": "⚠️",
     "desc": "Cuando hay clientes con facturas vencidas.", "config_fields": []},
]

ACTIONS: list[dict[str, Any]] = [
    {"type": "notify", "label": "Crear notificación", "icon": "🔔",
     "desc": "Avisa en la bandeja de SavvyFlow.",
     "config_fields": [
         {"key": "title", "label": "Título", "type": "text", "default": "{count} resultado(s)"},
         {"key": "body", "label": "Mensaje", "type": "textarea", "default": ""},
         {"key": "level", "label": "Nivel", "type": "select",
          "options": ["info", "warning", "danger"], "default": "info"},
     ]},
    {"type": "webhook", "label": "Llamar webhook", "icon": "🔗",
     "desc": "Envía los datos a una URL (POST).",
     "config_fields": [{"key": "url", "label": "URL", "type": "url", "default": ""}]},
    {"type": "whatsapp", "label": "Enviar WhatsApp", "icon": "💬",
     "desc": "Mensaje por WhatsApp (se activa en la Fase 4).",
     "config_fields": [
         {"key": "to", "label": "Para", "type": "text", "default": ""},
         {"key": "message", "label": "Mensaje", "type": "textarea", "default": ""},
     ]},
    {"type": "email", "label": "Enviar correo", "icon": "✉️",
     "desc": "Correo electrónico (se activa en la Fase 4).",
     "config_fields": [
         {"key": "to", "label": "Para", "type": "text", "default": ""},
         {"key": "subject", "label": "Asunto", "type": "text", "default": ""},
     ]},
]

CONDITIONS: list[dict[str, Any]] = [
    {"type": "field_compare", "label": "Filtrar por campo",
     "desc": "Solo continúa con los items que cumplen una comparación.",
     "ops": ["eq", "ne", "gt", "gte", "lt", "lte", "contains"]},
]


# ============================================================ Triggers → items


async def _trigger_items(
    db: AsyncSession, org_id: uuid.UUID, trigger_type: str, config: dict,
) -> list[dict[str, Any]]:
    if trigger_type == "manual":
        return [{"summary": "Ejecución manual"}]
    if trigger_type == "schedule_daily":
        from src.modules.savvy_ai.briefing import gather_metrics
        m = await gather_metrics(db, org_id)
        return [{"summary": "Resumen diario", **m}]
    if trigger_type == "pos_low_stock":
        rows = (await db.execute(text("""
            SELECT p.name AS product, p.sku, i.quantity, i.min_stock
            FROM pos_inventory i JOIN pos_products p ON p.id = i.product_id
            WHERE i.organization_id = :org AND i.min_stock > 0 AND i.quantity <= i.min_stock
            ORDER BY (i.min_stock - i.quantity) DESC
        """), {"org": org_id})).mappings().all()
        return [dict(r) for r in rows]
    if trigger_type == "memorial_overdue":
        from src.modules.savvy_ai.insights import memorial_collection_risk
        risk = await memorial_collection_risk(db, org_id)
        return risk["at_risk"]
    return []


# ============================================================ Condiciones


_OPS = {
    "eq": lambda a, b: str(a) == str(b),
    "ne": lambda a, b: str(a) != str(b),
    "gt": lambda a, b: _num(a) > _num(b),
    "gte": lambda a, b: _num(a) >= _num(b),
    "lt": lambda a, b: _num(a) < _num(b),
    "lte": lambda a, b: _num(a) <= _num(b),
    "contains": lambda a, b: str(b).lower() in str(a).lower(),
}


def _num(v: Any) -> float:
    try:
        return float(v)
    except Exception:
        return 0.0


def _apply_condition(items: list[dict], config: dict) -> list[dict]:
    field = config.get("field")
    op = config.get("op", "eq")
    value = config.get("value")
    fn = _OPS.get(op)
    if not field or fn is None:
        return items
    return [it for it in items if field in it and fn(it.get(field), value)]


# ============================================================ Acciones


def _render(template: str, ctx: dict) -> str:
    out = template or ""
    for k, v in ctx.items():
        out = out.replace("{" + k + "}", str(v))
    return out


async def _run_action(
    db: AsyncSession, org_id: uuid.UUID, wf: AutomationWorkflow, run: AutomationRun,
    step: AutomationStep, ctx: dict,
) -> dict[str, Any]:
    cfg = step.config or {}
    t = step.type
    if t == "notify":
        title = _render(cfg.get("title") or "{count} resultado(s)", ctx)
        body = _render(cfg.get("body") or "", ctx)
        notif = AutomationNotification(
            organization_id=org_id, workflow_id=wf.id, run_id=run.id,
            level=cfg.get("level", "info"), title=title[:200], body=body or None,
            link=cfg.get("link"),
        )
        db.add(notif)
        return {"action": "notify", "ok": True, "title": title}
    if t == "webhook":
        url = cfg.get("url")
        if not url:
            return {"action": "webhook", "ok": False, "error": "URL vacía"}
        try:
            async with httpx.AsyncClient(timeout=15) as http:
                resp = await http.post(url, json={
                    "workflow": wf.name, "count": ctx.get("count"),
                    "items": ctx.get("items", [])[:50],
                })
            return {"action": "webhook", "ok": resp.status_code < 400, "status": resp.status_code}
        except Exception as exc:  # noqa: BLE001
            return {"action": "webhook", "ok": False, "error": str(exc)[:200]}
    if t in ("whatsapp", "email"):
        # Stub: se activa en la Fase 4 (integración WhatsApp/correo).
        return {"action": t, "ok": True, "pending_integration": True,
                "would_send_to": cfg.get("to"), "note": "Se enviará al activar la Fase 4."}
    return {"action": t, "ok": False, "error": "acción desconocida"}


# ============================================================ Ejecución


async def run_workflow(
    db: AsyncSession,
    org_id: uuid.UUID,
    wf: AutomationWorkflow,
    steps: list[AutomationStep],
    *,
    source: str = "manual",
    only_if_matches: bool = False,
) -> AutomationRun:
    """Ejecuta un flujo completo. Devuelve el run (con log)."""
    run = AutomationRun(
        organization_id=org_id, workflow_id=wf.id, status="running",
        trigger_source=source, log=[],
    )
    db.add(run)
    await db.flush()
    log: list[dict[str, Any]] = []

    try:
        items = await _trigger_items(db, org_id, wf.trigger_type, wf.trigger_config or {})
        log.append({"step": "trigger", "type": wf.trigger_type, "items": len(items)})

        ordered = sorted(steps, key=lambda s: s.sort_order)
        for st in ordered:
            if st.kind == "condition":
                before = len(items)
                items = _apply_condition(items, st.config or {})
                log.append({"step": "condition", "type": st.type, "from": before, "to": len(items)})

        # Si es un trigger de datos y no hay items, se omite (no spamear).
        if only_if_matches and not items and wf.trigger_type in ("pos_low_stock", "memorial_overdue"):
            run.status = "skipped"
            run.items_matched = 0
            run.log = log + [{"step": "skip", "reason": "sin items"}]
            run.finished_at = _now()
            await db.flush()
            return run

        ctx = {
            "count": len(items),
            "items": items,
            "trigger": wf.trigger_type,
            "first": items[0] if items else {},
        }
        for st in ordered:
            if st.kind == "action":
                res = await _run_action(db, org_id, wf, run, st, ctx)
                log.append({"step": "action", **res})

        run.status = "succeeded"
        run.items_matched = len(items)
        run.log = log
        run.finished_at = _now()
        wf.run_count += 1
        wf.last_run_at = _now()
        wf.last_status = "succeeded"
        await db.flush()
        return run
    except Exception as exc:  # noqa: BLE001
        run.status = "failed"
        run.error = str(exc)[:500]
        run.log = log + [{"step": "error", "error": str(exc)[:300]}]
        run.finished_at = _now()
        wf.last_status = "failed"
        await db.flush()
        return run
