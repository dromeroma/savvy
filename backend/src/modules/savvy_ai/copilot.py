"""SavvyCopilot — asistente conversacional con Tool Use.

El LLM responde preguntas consultando datos reales a través de un registro de
herramientas (de solo lectura en esta fase). Cada llamada al modelo se mide.
Las herramientas reusan el Savvy Graph y consultas directas a las apps.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.modules.savvy_ai.client import ClaudeProvider, get_provider
from src.modules.savvy_ai.graph import universal_search
from src.modules.savvy_ai.usage import CallContext, check_quota, record_usage

COPILOT_SYSTEM = (
    "Eres SavvyCopilot, el asistente del ERP Savvy para una pyme en Colombia. "
    "Respondes en español, claro y breve. Cuando necesites datos, usa las "
    "herramientas disponibles — NUNCA inventes cifras. Si una herramienta no "
    "devuelve datos, dilo. Da montos en pesos colombianos con separador de miles. "
    "Si el usuario pide abrir o navegar a algo, sugiere la ruta correspondiente."
)


# ---------------- Herramientas (solo lectura) ----------------

async def _tool_universal_search(db, org_id, query: str = "", **_) -> dict[str, Any]:
    hits = await universal_search(db, org_id, query)
    return {"results": [
        {"module": h.module, "type": h.entity_type, "name": h.display_name,
         "document": h.document_number, "detail": h.subtitle, "route": h.route}
        for h in hits
    ]}


async def _tool_pos_sales(db, org_id, period: str = "today", **_) -> dict[str, Any]:
    rng = {
        "today": "created_at::date = now()::date",
        "week": "created_at >= now() - interval '7 days'",
        "month": "date_trunc('month', created_at) = date_trunc('month', now())",
    }.get(period, "created_at::date = now()::date")
    row = (await db.execute(text(f"""
        SELECT count(*) AS n, coalesce(sum(total),0) AS total
        FROM pos_sales
        WHERE organization_id = :org AND status <> 'cancelled' AND {rng}
    """), {"org": org_id})).mappings().first()
    return {"period": period, "sales_count": int(row["n"]), "total": float(row["total"])}


async def _tool_pos_low_stock(db, org_id, **_) -> dict[str, Any]:
    rows = (await db.execute(text("""
        SELECT p.name, i.quantity, i.min_stock
        FROM pos_inventory i JOIN pos_products p ON p.id = i.product_id
        WHERE i.organization_id = :org AND i.min_stock > 0 AND i.quantity <= i.min_stock
        ORDER BY (i.min_stock - i.quantity) DESC LIMIT 20
    """), {"org": org_id})).mappings().all()
    return {"low_stock": [
        {"product": r["name"], "quantity": float(r["quantity"]), "min": float(r["min_stock"])}
        for r in rows
    ]}


async def _tool_memorial_receivables(db, org_id, **_) -> dict[str, Any]:
    row = (await db.execute(text("""
        SELECT coalesce(sum(balance),0) AS pending,
               coalesce(sum(CASE WHEN due_date < now()::date THEN balance ELSE 0 END),0) AS overdue
        FROM memorial_invoices
        WHERE organization_id = :org AND coalesce(balance,0) > 0
    """), {"org": org_id})).mappings().first()
    return {"pending_balance": float(row["pending"]), "overdue_balance": float(row["overdue"])}


async def _tool_hr_headcount(db, org_id, **_) -> dict[str, Any]:
    rows = (await db.execute(text("""
        SELECT status, count(*) AS n FROM hr_employees
        WHERE organization_id = :org GROUP BY status
    """), {"org": org_id})).mappings().all()
    by = {r["status"]: int(r["n"]) for r in rows}
    return {"by_status": by, "active": by.get("active", 0), "total": sum(by.values())}


TOOLS: list[dict[str, Any]] = [
    {
        "name": "universal_search",
        "description": "Busca una persona o entidad (cliente, empleado, afiliado, suscriptor, lead) en TODOS los módulos por nombre o documento.",
        "input_schema": {"type": "object", "properties": {"query": {"type": "string"}}, "required": ["query"]},
        "fn": _tool_universal_search,
    },
    {
        "name": "pos_sales_summary",
        "description": "Resumen de ventas del POS para un período: today, week o month.",
        "input_schema": {"type": "object", "properties": {"period": {"type": "string", "enum": ["today", "week", "month"]}}},
        "fn": _tool_pos_sales,
    },
    {
        "name": "pos_low_stock",
        "description": "Productos del POS cuyo stock está en o por debajo del mínimo.",
        "input_schema": {"type": "object", "properties": {}},
        "fn": _tool_pos_low_stock,
    },
    {
        "name": "memorial_receivables",
        "description": "Cartera por cobrar y cartera vencida de la funeraria (Memorial).",
        "input_schema": {"type": "object", "properties": {}},
        "fn": _tool_memorial_receivables,
    },
    {
        "name": "hr_headcount",
        "description": "Conteo de empleados de Talento Humano por estado (activos, etc.).",
        "input_schema": {"type": "object", "properties": {}},
        "fn": _tool_hr_headcount,
    },
]

_TOOL_BY_NAME = {t["name"]: t for t in TOOLS}
_TOOL_SCHEMAS = [{k: t[k] for k in ("name", "description", "input_schema")} for t in TOOLS]


@dataclass
class CopilotResult:
    answer: str
    tools_used: list[str] = field(default_factory=list)


async def ask(
    db: AsyncSession,
    org_id: uuid.UUID,
    message: str,
    *,
    user_id: uuid.UUID | None = None,
    max_iters: int = 5,
) -> CopilotResult:
    """Ejecuta el loop agentic: pregunta → (herramientas)* → respuesta."""
    await check_quota(db, org_id)
    provider: ClaudeProvider = await get_provider(db)

    messages: list[dict[str, Any]] = [{"role": "user", "content": message}]
    tools_used: list[str] = []

    for _ in range(max_iters):
        result = await provider.complete(
            messages=messages, tier="sonnet", system=COPILOT_SYSTEM,
            tools=_TOOL_SCHEMAS, max_tokens=1500,
        )
        await record_usage(
            db,
            CallContext(
                organization_id=org_id, user_id=user_id, app_code="copilot",
                feature="copilot", action="copilot.ask",
                prompt_key="copilot.system", prompt_version="v1", tier="sonnet",
            ),
            result,
        )

        content = result.raw.get("content", []) or []
        stop = result.raw.get("stop_reason")
        if stop != "tool_use":
            await db.commit()
            text_out = "".join(b.get("text", "") for b in content if b.get("type") == "text").strip()
            return CopilotResult(answer=text_out or result.text, tools_used=tools_used)

        # Ejecutar todas las herramientas solicitadas
        messages.append({"role": "assistant", "content": content})
        tool_results = []
        for block in content:
            if block.get("type") != "tool_use":
                continue
            name = block.get("name")
            tool = _TOOL_BY_NAME.get(name)
            tools_used.append(name)
            try:
                out = await tool["fn"](db, org_id, **(block.get("input") or {})) if tool else {"error": "tool desconocida"}
            except Exception as exc:  # noqa: BLE001
                out = {"error": str(exc)[:200]}
            tool_results.append({
                "type": "tool_result", "tool_use_id": block.get("id"),
                "content": _json_compact(out),
            })
        messages.append({"role": "user", "content": tool_results})

    await db.commit()
    return CopilotResult(answer="No pude completar la consulta en los pasos disponibles.", tools_used=tools_used)


def _json_compact(obj: Any) -> str:
    import json
    return json.dumps(obj, ensure_ascii=False, default=str)
