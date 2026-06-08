"""SavvyInsights — inteligencia predictiva y recomendaciones (Fase 3).

Análisis determinista (no requiere IA) que convierte los datos en acciones:
  - POS: sugerencias de reorden, productos estancados, recomendaciones de promo
  - Memorial: riesgo de cartera (clientes/contratos en mora)

La capa de IA (narrativa) es opcional y se monta encima; estos cálculos
funcionan hoy mismo sin API key.
"""

from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Parámetros por defecto (configurables más adelante por organización).
LEAD_TIME_DAYS = 7        # días que tarda en llegar un pedido al proveedor
SAFETY_DAYS = 7           # colchón de seguridad
VELOCITY_WINDOW = 30      # ventana para calcular velocidad de venta
STALE_DAYS = 45           # sin ventas en este período = estancado


# ============================================================ POS


async def pos_inventory_insights(db: AsyncSession, org_id: uuid.UUID) -> dict[str, Any]:
    """Reorden, riesgo de agotamiento y productos estancados."""
    # Velocidad de venta por producto (unidades/día) en la ventana.
    rows = (await db.execute(text(f"""
        WITH velocity AS (
            SELECT sl.product_id,
                   coalesce(sum(sl.quantity),0) AS sold,
                   coalesce(sum(sl.quantity),0) / {VELOCITY_WINDOW}.0 AS per_day
            FROM pos_sale_lines sl
            JOIN pos_sales s ON s.id = sl.sale_id
            WHERE s.organization_id = :org
              AND s.status <> 'cancelled'
              AND s.created_at >= now() - interval '{VELOCITY_WINDOW} days'
            GROUP BY sl.product_id
        ),
        stock AS (
            SELECT product_id, coalesce(sum(quantity),0) AS qty,
                   coalesce(max(min_stock),0) AS min_stock
            FROM pos_inventory WHERE organization_id = :org
            GROUP BY product_id
        )
        SELECT p.id::text AS id, p.name, p.sku, p.cost,
               coalesce(st.qty,0) AS qty,
               coalesce(st.min_stock,0) AS min_stock,
               coalesce(v.sold,0) AS sold,
               coalesce(v.per_day,0) AS per_day
        FROM pos_products p
        LEFT JOIN stock st ON st.product_id = p.id
        LEFT JOIN velocity v ON v.product_id = p.id
        WHERE p.organization_id = :org AND p.tracks_inventory = true AND p.status = 'active'
    """), {"org": org_id})).mappings().all()

    reorder: list[dict[str, Any]] = []
    stale: list[dict[str, Any]] = []
    for r in rows:
        qty = float(r["qty"])
        per_day = float(r["per_day"])
        sold = float(r["sold"])
        if per_day > 0:
            days_left = qty / per_day
            if days_left < (LEAD_TIME_DAYS + SAFETY_DAYS):
                target = per_day * (LEAD_TIME_DAYS + SAFETY_DAYS * 2)
                suggest = max(0, round(target - qty))
                if suggest > 0:
                    reorder.append({
                        "product": r["name"], "sku": r["sku"],
                        "current_stock": qty, "per_day": round(per_day, 2),
                        "days_left": round(days_left, 1),
                        "suggested_qty": suggest,
                        "est_cost": round(suggest * float(r["cost"] or 0), 2),
                        "urgency": "alta" if days_left < LEAD_TIME_DAYS else "media",
                    })
        elif qty > 0:
            # Con stock pero sin ventas en la ventana → estancado.
            stale.append({
                "product": r["name"], "sku": r["sku"],
                "current_stock": qty,
                "tied_capital": round(qty * float(r["cost"] or 0), 2),
            })

    reorder.sort(key=lambda x: x["days_left"])
    stale.sort(key=lambda x: x["tied_capital"], reverse=True)
    return {
        "reorder": reorder[:25],
        "stale": stale[:25],
        "reorder_count": len(reorder),
        "stale_count": len(stale),
    }


async def pos_promo_recommendations(db: AsyncSession, org_id: uuid.UUID) -> dict[str, Any]:
    """Empareja un producto estancado con un best-seller de su misma categoría."""
    rows = (await db.execute(text(f"""
        WITH sales AS (
            SELECT sl.product_id, coalesce(sum(sl.quantity),0) AS sold
            FROM pos_sale_lines sl JOIN pos_sales s ON s.id = sl.sale_id
            WHERE s.organization_id = :org AND s.status <> 'cancelled'
              AND s.created_at >= now() - interval '{VELOCITY_WINDOW} days'
            GROUP BY sl.product_id
        )
        SELECT p.id::text AS id, p.name, p.category_id::text AS cat,
               coalesce(s.sold,0) AS sold,
               coalesce((SELECT sum(quantity) FROM pos_inventory i WHERE i.product_id = p.id),0) AS qty
        FROM pos_products p LEFT JOIN sales s ON s.product_id = p.id
        WHERE p.organization_id = :org AND p.status = 'active' AND p.category_id IS NOT NULL
    """), {"org": org_id})).mappings().all()

    by_cat: dict[str, list[dict]] = {}
    for r in rows:
        by_cat.setdefault(r["cat"], []).append(dict(r))

    promos: list[dict[str, Any]] = []
    for cat, items in by_cat.items():
        sellers = sorted(items, key=lambda x: float(x["sold"]), reverse=True)
        top = sellers[0] if sellers and float(sellers[0]["sold"]) > 0 else None
        stale = [i for i in items if float(i["sold"]) == 0 and float(i["qty"]) > 0]
        if top and stale:
            promos.append({
                "anchor": top["name"], "anchor_sold": float(top["sold"]),
                "promote": stale[0]["name"], "promote_stock": float(stale[0]["qty"]),
                "idea": f"Combo: lleva «{top['name']}» y «{stale[0]['name']}» con descuento.",
            })
    return {"promos": promos[:15], "count": len(promos)}


# ============================================================ Memorial


async def memorial_collection_risk(db: AsyncSession, org_id: uuid.UUID) -> dict[str, Any]:
    """Contratos exequiales con riesgo de cartera (facturas vencidas)."""
    rows = (await db.execute(text("""
        SELECT c.id::text AS id, c.code,
               trim(coalesce(c.titular_business_name,
                    coalesce(c.titular_first_name,'') || ' ' || coalesce(c.titular_last_name,''))) AS name,
               c.titular_mobile AS phone,
               c.status AS contract_status,
               count(i.id) FILTER (WHERE i.balance > 0 AND i.due_date < now()::date) AS overdue_count,
               coalesce(sum(i.balance) FILTER (WHERE i.balance > 0 AND i.due_date < now()::date),0) AS overdue_amount,
               coalesce(sum(i.balance) FILTER (WHERE i.balance > 0),0) AS pending_amount,
               max((now()::date - i.due_date)) FILTER (WHERE i.balance > 0 AND i.due_date < now()::date) AS max_days_late
        FROM memorial_exequial_contracts c
        LEFT JOIN memorial_invoices i ON i.contract_id = c.id
        WHERE c.organization_id = :org
        GROUP BY c.id, c.code, name, c.titular_mobile, c.status
        HAVING count(i.id) FILTER (WHERE i.balance > 0 AND i.due_date < now()::date) > 0
        ORDER BY overdue_amount DESC
    """), {"org": org_id})).mappings().all()

    at_risk: list[dict[str, Any]] = []
    total_overdue = 0.0
    for r in rows:
        days = int(r["max_days_late"] or 0)
        overdue_count = int(r["overdue_count"])
        amount = float(r["overdue_amount"])
        total_overdue += amount
        if days > 90 or overdue_count >= 3:
            tier = "alto"
        elif days > 30 or overdue_count >= 2:
            tier = "medio"
        else:
            tier = "bajo"
        at_risk.append({
            "contract_id": r["id"], "code": r["code"], "name": r["name"] or "(sin nombre)",
            "phone": r["phone"], "contract_status": r["contract_status"],
            "overdue_count": overdue_count, "overdue_amount": amount,
            "pending_amount": float(r["pending_amount"]), "days_late": days,
            "risk_tier": tier,
            "action": (
                "Llamar hoy — riesgo de pérdida" if tier == "alto"
                else "Enviar recordatorio de pago" if tier == "medio"
                else "Monitorear"
            ),
        })
    by_tier = {"alto": 0, "medio": 0, "bajo": 0}
    for x in at_risk:
        by_tier[x["risk_tier"]] += 1
    return {
        "at_risk": at_risk[:50],
        "total_at_risk": len(at_risk),
        "total_overdue_amount": round(total_overdue, 2),
        "by_tier": by_tier,
    }


# ============================================================ Resumen combinado


async def insights_summary(db: AsyncSession, org_id: uuid.UUID) -> dict[str, Any]:
    """Tarjetas de titulares para mostrar de un vistazo."""
    pos = await pos_inventory_insights(db, org_id)
    promos = await pos_promo_recommendations(db, org_id)
    mem = await memorial_collection_risk(db, org_id)
    cards: list[dict[str, Any]] = []
    if pos["reorder_count"]:
        cards.append({"icon": "📦", "tone": "warn",
                      "title": f"{pos['reorder_count']} producto(s) por reabastecer",
                      "detail": "Stock bajo según tu ritmo de ventas.", "link": "/pos/insights"})
    if pos["stale_count"]:
        cards.append({"icon": "🐌", "tone": "info",
                      "title": f"{pos['stale_count']} producto(s) estancado(s)",
                      "detail": "Con stock pero sin ventas recientes.", "link": "/pos/insights"})
    if promos["count"]:
        cards.append({"icon": "🎯", "tone": "violet",
                      "title": f"{promos['count']} idea(s) de promoción",
                      "detail": "Combina estancados con best-sellers.", "link": "/pos/insights"})
    if mem["total_at_risk"]:
        cards.append({"icon": "⚠️", "tone": "danger",
                      "title": f"{mem['total_at_risk']} cliente(s) en riesgo de cartera",
                      "detail": f"$ {mem['total_overdue_amount']:,.0f} vencidos.".replace(",", "."),
                      "link": "/memorial/risk"})
    return {"cards": cards}
