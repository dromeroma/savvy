"""Aplicador de extracciones de IA al inventario POS.

Cuando una factura de compra extraída por SavvyScan se confirma, esto traduce
los ítems a entidades reales del POS: crea/actualiza productos, ajusta costos y
registra movimientos de compra (stock +). Es el corazón del flujo
"factura → inventario" de la Fase 1.
"""

from __future__ import annotations

import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.pos.catalog.models import PosLocation, PosProduct
from src.apps.pos.inventory.models import PosInventory, PosStockMovement

# Margen por defecto al sugerir precio de venta sobre el costo (editable luego).
DEFAULT_MARGIN = Decimal("1.30")


def _to_decimal(v: Any) -> Decimal:
    try:
        return Decimal(str(v))
    except Exception:
        return Decimal("0")


async def _default_location(db: AsyncSession, org_id: uuid.UUID) -> PosLocation:
    loc = (await db.execute(
        select(PosLocation)
        .where(PosLocation.organization_id == org_id, PosLocation.status == "active")
        .order_by(PosLocation.created_at)
        .limit(1)
    )).scalar_one_or_none()
    if loc is not None:
        return loc
    loc = PosLocation(organization_id=org_id, code="PRINCIPAL", name="Sede principal", status="active")
    db.add(loc)
    await db.flush()
    return loc


async def _find_product(
    db: AsyncSession, org_id: uuid.UUID, sku: str | None, name: str,
) -> PosProduct | None:
    if sku:
        p = (await db.execute(
            select(PosProduct).where(
                PosProduct.organization_id == org_id, PosProduct.sku == sku,
            )
        )).scalar_one_or_none()
        if p:
            return p
    # match por nombre exacto (case-insensitive)
    return (await db.execute(
        select(PosProduct).where(
            PosProduct.organization_id == org_id,
            func.lower(PosProduct.name) == name.strip().lower(),
        ).limit(1)
    )).scalar_one_or_none()


async def _next_sku(db: AsyncSession, org_id: uuid.UUID) -> str:
    count = (await db.execute(
        select(func.count(PosProduct.id)).where(PosProduct.organization_id == org_id)
    )).scalar() or 0
    return f"AI-{count + 1:05d}"


async def apply_purchase_invoice(
    db: AsyncSession,
    org_id: uuid.UUID,
    data: dict[str, Any],
    *,
    user_id: uuid.UUID | None = None,
) -> dict[str, Any]:
    """Aplica una factura de compra confirmada al inventario.

    Devuelve un resumen para el audit/UI. No hace commit (lo hace el caller).
    """
    location = await _default_location(db, org_id)
    items = data.get("line_items") or []

    created = 0
    updated = 0
    total_units = Decimal("0")
    total_cost = Decimal("0")
    details: list[dict[str, Any]] = []

    for item in items:
        name = (item.get("description") or "").strip()
        if not name:
            continue
        sku = item.get("sku") or None
        qty = _to_decimal(item.get("quantity") or 0)
        unit_cost = _to_decimal(item.get("unit_cost") or 0)
        if qty <= 0:
            continue

        product = await _find_product(db, org_id, sku, name)
        if product is None:
            product = PosProduct(
                organization_id=org_id,
                sku=sku or await _next_sku(db, org_id),
                name=name,
                cost=float(unit_cost),
                price=float((unit_cost * DEFAULT_MARGIN).quantize(Decimal("0.01"))) if unit_cost > 0 else 0,
                tracks_inventory=True,
                status="active",
            )
            db.add(product)
            await db.flush()
            created += 1
            action = "created"
        else:
            if unit_cost > 0:
                product.cost = float(unit_cost)
            updated += 1
            action = "updated"

        # Movimiento de compra (stock +) + materializar inventario
        inv = (await db.execute(
            select(PosInventory).where(
                PosInventory.organization_id == org_id,
                PosInventory.product_id == product.id,
                PosInventory.variant_id.is_(None),
                PosInventory.location_id == location.id,
            )
        )).scalar_one_or_none()
        if inv is None:
            inv = PosInventory(
                organization_id=org_id, product_id=product.id,
                location_id=location.id, quantity=0,
            )
            db.add(inv)
            await db.flush()

        movement = PosStockMovement(
            organization_id=org_id, product_id=product.id, location_id=location.id,
            movement_type="purchase", quantity=float(qty), unit_cost=float(unit_cost),
            reference_type="ai_purchase_invoice", reference_id=None,
            notes=f"SavvyScan · proveedor {data.get('supplier_name') or '—'}",
            performed_by=user_id,
        )
        db.add(movement)
        inv.quantity = float(_to_decimal(inv.quantity) + qty)

        total_units += qty
        total_cost += qty * unit_cost
        details.append({
            "product": name, "sku": product.sku, "action": action,
            "quantity": float(qty), "unit_cost": float(unit_cost),
        })

    await db.flush()
    return {
        "location": location.name,
        "supplier_name": data.get("supplier_name"),
        "invoice_number": data.get("invoice_number"),
        "products_created": created,
        "products_updated": updated,
        "total_units": float(total_units),
        "total_cost": float(total_cost),
        "items": details,
    }
