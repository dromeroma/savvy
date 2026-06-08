"""Seed idempotente de datos POS para demo (org memorial-demo).

Crea sede, categorías, productos, inventario (con stock bajo y estancados) y ~30
días de ventas, para que SavvyScan e Insights predictivos tengan vida:
  - productos de alta rotación con poco stock → sugerencia de reorden
  - productos con stock sin ventas → estancados
  - estancado + best-seller en la misma categoría → idea de promo

Uso: python backend/scripts/seed_pos_demo.py [--dry-run]
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text  # noqa: E402

from src.core.database import async_session_factory, engine  # noqa: E402

ORG_SLUG = "memorial-demo"
random.seed(42)  # determinista

CATEGORIES = [("BEB", "Bebidas"), ("SNK", "Snacks"), ("LAC", "Lácteos"), ("ASE", "Aseo")]

# (sku, nombre, categoría, costo, precio, stock, min_stock, ventas_dia_aprox)
PRODUCTS = [
    ("BEB-001", "Gaseosa 1.5L", "BEB", 2800, 4500, 18, 12, 4.0),     # rota mucho, stock bajo → reorden
    ("BEB-002", "Agua 600ml", "BEB", 800, 1500, 60, 20, 3.0),
    ("BEB-003", "Jugo Hit 500ml", "BEB", 1500, 2500, 8, 10, 2.5),    # bajo mínimo → reorden urgente
    ("BEB-004", "Energizante", "BEB", 3500, 6000, 40, 8, 0.0),       # estancado (sin ventas)
    ("SNK-001", "Papas 45g", "SNK", 1200, 2000, 25, 15, 3.5),
    ("SNK-002", "Galletas Festival", "SNK", 900, 1600, 50, 15, 2.0),
    ("SNK-003", "Maní salado", "SNK", 1800, 3000, 30, 6, 0.0),       # estancado
    ("SNK-004", "Chocolatina Jet", "SNK", 700, 1300, 12, 10, 4.5),   # rota mucho, stock bajo → reorden
    ("LAC-001", "Leche 1L", "LAC", 3200, 4800, 22, 15, 3.0),
    ("LAC-002", "Yogurt 1L", "LAC", 4500, 6500, 9, 10, 1.5),         # bajo mínimo
    ("LAC-003", "Queso campesino", "LAC", 8000, 12000, 15, 5, 0.0),  # estancado caro
    ("ASE-001", "Jabón rey", "ASE", 1100, 1900, 40, 12, 1.0),
    ("ASE-002", "Papel higiénico x4", "ASE", 4200, 6500, 28, 10, 2.0),
    ("ASE-003", "Detergente 500g", "ASE", 3800, 5800, 35, 8, 0.0),   # estancado
]


async def main(dry: bool) -> None:
    print("=" * 70)
    print("SavvyPOS · seed de datos demo (memorial-demo)")
    print("=" * 70)
    async with async_session_factory() as s:
        async with s.begin():
            org = await s.scalar(text("SELECT id FROM organizations WHERE slug = :sl"), {"sl": ORG_SLUG})
            if not org:
                print(f"❌ Org '{ORG_SLUG}' no existe.")
                return

            # Guard: NUNCA sembrar POS en una org que no tiene la app 'pos' activa
            # (evita contaminar p.ej. una funeraria con datos de POS).
            has_pos = await s.scalar(text("""
                SELECT 1 FROM organization_apps oa JOIN app_registry ar ON ar.id = oa.app_id
                WHERE oa.organization_id = :o AND ar.code = 'pos' AND oa.status = 'active' LIMIT 1
            """), {"o": org})
            if not has_pos:
                print(f"❌ La org '{ORG_SLUG}' NO tiene la app 'pos' activa. Abortando "
                      "(no se siembra POS en orgs sin POS). Cambia ORG_SLUG a una org con POS.")
                return

            existing = await s.scalar(
                text("SELECT count(*) FROM pos_products WHERE organization_id = :o"), {"o": org}
            )
            if existing and not dry:
                print(f"  Ya hay {existing} productos POS — nada que sembrar (idempotente).")
                return

            # Sede
            loc = await s.scalar(text(
                "SELECT id FROM pos_locations WHERE organization_id = :o LIMIT 1"), {"o": org})
            if not loc:
                loc = uuid.uuid4()
                if not dry:
                    await s.execute(text("""
                        INSERT INTO pos_locations (id, organization_id, code, name, status, created_at, updated_at)
                        VALUES (:id, :o, 'PRINCIPAL', 'Sede principal', 'active', now(), now())
                    """), {"id": loc, "o": org})

            # Categorías
            cat_ids: dict[str, uuid.UUID] = {}
            for code, name in CATEGORIES:
                cid = uuid.uuid4()
                cat_ids[code] = cid
                if not dry:
                    await s.execute(text("""
                        INSERT INTO pos_categories (id, organization_id, code, name, sort_order, status, created_at, updated_at)
                        VALUES (:id, :o, :c, :n, 0, 'active', now(), now())
                    """), {"id": cid, "o": org, "c": code, "n": name})

            # Productos + inventario
            prod_ids: dict[str, uuid.UUID] = {}
            for sku, name, cat, cost, price, stock, minst, _vel in PRODUCTS:
                pid = uuid.uuid4()
                prod_ids[sku] = pid
                if not dry:
                    await s.execute(text("""
                        INSERT INTO pos_products
                          (id, organization_id, category_id, sku, name, product_type, price, cost,
                           tracks_inventory, attributes, status, created_at, updated_at)
                        VALUES (:id, :o, :cat, :sku, :n, 'simple', :p, :c, true, '{}'::jsonb, 'active', now(), now())
                    """), {"id": pid, "o": org, "cat": cat_ids[cat], "sku": sku, "n": name, "p": price, "c": cost})
                    await s.execute(text("""
                        INSERT INTO pos_inventory
                          (id, organization_id, product_id, location_id, quantity, min_stock, created_at, updated_at)
                        VALUES (:id, :o, :pid, :loc, :q, :m, now(), now())
                    """), {"id": uuid.uuid4(), "o": org, "pid": pid, "loc": loc, "q": stock, "m": minst})

            # ~30 días de ventas (según velocidad por producto)
            sales = 0
            lines = 0
            for day in range(30, 0, -1):
                day_dt = datetime.utcnow() - timedelta(days=day)
                # agrupa unas ventas por día
                basket: list[tuple[str, int, int, int]] = []
                for sku, name, cat, cost, price, stock, minst, vel in PRODUCTS:
                    qty = int(round(vel * random.uniform(0.6, 1.4)))
                    if qty > 0:
                        basket.append((sku, name, qty, price))
                if not basket:
                    continue
                # 1-3 transacciones por día repartiendo el basket
                random.shuffle(basket)
                chunks = [basket[i::2] for i in range(2)]
                for ci, chunk in enumerate(chunks):
                    if not chunk:
                        continue
                    sale_id = uuid.uuid4()
                    subtotal = sum(q * p for _, _, q, p in chunk)
                    when = day_dt + timedelta(hours=10 + ci * 4)
                    if not dry:
                        await s.execute(text("""
                            INSERT INTO pos_sales
                              (id, organization_id, sale_number, location_id, subtotal, discount_amount,
                               tax_amount, total, payment_method, payment_details, status, created_at, updated_at)
                            VALUES (:id, :o, :num, :loc, :sub, 0, 0, :sub, 'cash', '{}'::jsonb, 'completed', :ts, :ts)
                        """), {"id": sale_id, "o": org, "num": f"V-{when:%Y%m%d}-{ci+1}",
                               "loc": loc, "sub": subtotal, "ts": when})
                        for sku, name, q, p in chunk:
                            await s.execute(text("""
                                INSERT INTO pos_sale_lines
                                  (id, sale_id, product_id, product_name, sku, quantity, unit_price,
                                   discount, tax_rate, tax_amount, line_total, created_at, updated_at)
                                VALUES (:id, :sid, :pid, :n, :sku, :q, :p, 0, 0, 0, :lt, :ts, :ts)
                            """), {"id": uuid.uuid4(), "sid": sale_id, "pid": prod_ids[sku], "n": name,
                                   "sku": sku, "q": q, "p": p, "lt": q * p, "ts": when})
                            lines += 1
                    sales += 1

            if dry:
                await s.rollback()
            print(f"  {'(dry) ' if dry else ''}sede=1 · categorías={len(CATEGORIES)} · productos={len(PRODUCTS)} · ventas={sales} · líneas={lines}")
    print("\n✓ Seed POS completo." if not dry else "\nDRY-RUN — nada persistido.")
    await engine.dispose()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    asyncio.run(main(ap.parse_args().dry_run))
