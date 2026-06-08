"""Savvy Briefing — resumen proactivo diario.

Agrega métricas clave cross-app y las redacta en lenguaje natural. Si la IA
está configurada, usa el LLM; si no, cae a una narrativa con plantilla para que
funcione desde hoy (sin API key).
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.savvy_ai.client import AiNotConfiguredError, get_provider
from src.modules.savvy_ai.usage import CallContext, record_usage


def _fmt(n: float) -> str:
    return f"{n:,.0f}".replace(",", ".")


async def _safe(db, sql: str, org_id: uuid.UUID) -> dict[str, Any]:
    try:
        return dict((await db.execute(text(sql), {"org": org_id})).mappings().first() or {})
    except Exception:
        return {}


async def gather_metrics(db: AsyncSession, org_id: uuid.UUID) -> dict[str, Any]:
    """Reúne las métricas del día de las apps activas. Tolera tablas ausentes."""
    pos = await _safe(db, """
        SELECT count(*) AS sales, coalesce(sum(total),0) AS total
        FROM pos_sales
        WHERE organization_id = :org AND status <> 'cancelled'
          AND created_at::date = now()::date
    """, org_id)
    low = await _safe(db, """
        SELECT count(*) AS n FROM pos_inventory
        WHERE organization_id = :org AND min_stock > 0 AND quantity <= min_stock
    """, org_id)
    mem = await _safe(db, """
        SELECT coalesce(sum(balance),0) AS pending,
               coalesce(sum(CASE WHEN due_date < now()::date THEN balance ELSE 0 END),0) AS overdue
        FROM memorial_invoices
        WHERE organization_id = :org AND coalesce(balance,0) > 0
    """, org_id)
    hr = await _safe(db, """
        SELECT count(*) FILTER (WHERE status='active') AS active,
               count(*) FILTER (WHERE status IN ('on_leave','suspended')) AS away
        FROM hr_employees WHERE organization_id = :org
    """, org_id)
    return {
        "pos_sales_today": int(pos.get("sales", 0) or 0),
        "pos_total_today": float(pos.get("total", 0) or 0),
        "pos_low_stock": int(low.get("n", 0) or 0),
        "memorial_pending": float(mem.get("pending", 0) or 0),
        "memorial_overdue": float(mem.get("overdue", 0) or 0),
        "hr_active": int(hr.get("active", 0) or 0),
        "hr_away": int(hr.get("away", 0) or 0),
    }


def _template_narrative(m: dict[str, Any]) -> list[str]:
    lines: list[str] = []
    if m["pos_sales_today"] or m["pos_total_today"]:
        lines.append(f"Hoy llevas {m['pos_sales_today']} venta(s) por $ {_fmt(m['pos_total_today'])} en el POS.")
    if m["pos_low_stock"]:
        lines.append(f"⚠ {m['pos_low_stock']} producto(s) están en o bajo el stock mínimo — conviene reabastecer.")
    if m["memorial_overdue"]:
        lines.append(f"Cartera vencida en Memorial: $ {_fmt(m['memorial_overdue'])} (de $ {_fmt(m['memorial_pending'])} por cobrar).")
    elif m["memorial_pending"]:
        lines.append(f"Cartera por cobrar en Memorial: $ {_fmt(m['memorial_pending'])}.")
    if m["hr_away"]:
        lines.append(f"En Talento Humano hay {m['hr_active']} activos y {m['hr_away']} ausentes (licencia/suspensión).")
    elif m["hr_active"]:
        lines.append(f"Talento Humano: {m['hr_active']} empleados activos, sin ausencias.")
    if not lines:
        lines.append("Sin actividad relevante por ahora. Cuando empieces a operar, aquí verás tu resumen del día.")
    return lines


async def generate(
    db: AsyncSession, org_id: uuid.UUID, *, user_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Genera el briefing. Narrativa IA si hay API key; si no, plantilla."""
    metrics = await gather_metrics(db, org_id)

    # Intento con IA
    try:
        provider = await get_provider(db)
    except AiNotConfiguredError:
        return {"narrative": _template_narrative(metrics), "metrics": metrics, "generated_by": "template"}

    facts = "; ".join(f"{k}={v}" for k, v in metrics.items())
    try:
        result = await provider.complete(
            messages=[{"role": "user", "content": (
                "Redacta un resumen ejecutivo del día para el dueño de un negocio, "
                "en 3-5 frases cortas, en español, tono cercano y profesional. "
                "Usa SOLO estos datos (no inventes), montos en pesos con separador de miles. "
                f"Datos: {facts}. Empieza con un saludo breve."
            )}],
            tier="haiku", max_tokens=400,
        )
        await record_usage(
            db,
            CallContext(
                organization_id=org_id, user_id=user_id, app_code="briefing",
                feature="briefing", action="briefing.generate",
                prompt_key="briefing.daily", prompt_version="v1", tier="haiku",
            ),
            result,
        )
        await db.commit()
        lines = [ln.strip("-• ") for ln in result.text.split("\n") if ln.strip()]
        return {"narrative": lines or _template_narrative(metrics), "metrics": metrics, "generated_by": "ai"}
    except Exception:
        return {"narrative": _template_narrative(metrics), "metrics": metrics, "generated_by": "template"}
