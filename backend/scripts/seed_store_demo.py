"""Crea una TIENDA demo (org propia) con POS activo, un usuario owner y datos.

A diferencia de seed_pos_demo (que exige una org con POS ya activo), este script
crea TODO: organización, usuario de login, membresía owner, activación de la app
'pos' y los datos (productos, inventario, 30 días de ventas). Aislado: los datos
viven solo en esta org.

Login del demo:
    email:    admin@tienda-demo.com
    password: Tienda1234!

Uso: python backend/scripts/seed_store_demo.py
"""

from __future__ import annotations

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
from src.core.security import hash_password  # noqa: E402
from scripts.seed_pos_demo import CATEGORIES, PRODUCTS  # noqa: E402

ORG_SLUG = "tienda-demo"
ORG_NAME = "Minimarket La Esquina"
ADMIN_EMAIL = "admin@tienda-demo.com"
ADMIN_PASSWORD = "Tienda1234!"
random.seed(7)


async def main() -> None:
    print("=" * 70)
    print("SavvyPOS · seed de TIENDA demo (org + usuario + POS + datos)")
    print("=" * 70)
    async with async_session_factory() as s:
        async with s.begin():
            # 1) Organización
            org = await s.scalar(text("SELECT id FROM organizations WHERE slug = :sl"), {"sl": ORG_SLUG})
            if not org:
                org = uuid.uuid4()
                await s.execute(text("""
                    INSERT INTO organizations (id, name, slug, type, settings, created_at, updated_at)
                    VALUES (:id, :n, :sl, 'business', '{}'::jsonb, now(), now())
                """), {"id": org, "n": ORG_NAME, "sl": ORG_SLUG})
                print(f"  + organización {ORG_NAME}")
            else:
                print(f"  ~ organización {ORG_NAME} (ya existía)")

            # 2) Usuario owner
            uid = await s.scalar(text("SELECT id FROM public.users WHERE email = :e"), {"e": ADMIN_EMAIL})
            if not uid:
                uid = uuid.uuid4()
                await s.execute(text("""
                    INSERT INTO public.users (id, name, email, password_hash, created_at, updated_at)
                    VALUES (:id, :n, :e, :ph, now(), now())
                """), {"id": uid, "n": "Admin Tienda", "e": ADMIN_EMAIL, "ph": hash_password(ADMIN_PASSWORD)})
                print(f"  + usuario {ADMIN_EMAIL}")
            else:
                # asegura el password conocido
                await s.execute(text("UPDATE public.users SET password_hash = :ph WHERE id = :id"),
                                {"ph": hash_password(ADMIN_PASSWORD), "id": uid})
                print(f"  ~ usuario {ADMIN_EMAIL} (password reseteado)")

            # 3) Membresía owner
            has_mem = await s.scalar(text(
                "SELECT 1 FROM memberships WHERE organization_id = :o AND user_id = :u"), {"o": org, "u": uid})
            if not has_mem:
                await s.execute(text("""
                    INSERT INTO memberships (id, organization_id, user_id, role, joined_at, created_at, updated_at)
                    VALUES (:id, :o, :u, 'owner', now(), now(), now())
                """), {"id": uuid.uuid4(), "o": org, "u": uid})
                print("  + membresía owner")

            # 4) Activar app POS
            pos_app = await s.scalar(text("SELECT id FROM app_registry WHERE code = 'pos'"))
            has_app = await s.scalar(text(
                "SELECT 1 FROM organization_apps WHERE organization_id = :o AND app_id = :a"),
                {"o": org, "a": pos_app})
            if not has_app:
                await s.execute(text("""
                    INSERT INTO organization_apps (id, organization_id, app_id, status, activated_at, settings, created_at, updated_at)
                    VALUES (:id, :o, :a, 'active', now(), '{}'::jsonb, now(), now())
                """), {"id": uuid.uuid4(), "o": org, "a": pos_app})
                print("  + app POS activada")

            # 5) Datos POS (idempotente: si ya hay productos, no reseed)
            existing = await s.scalar(text("SELECT count(*) FROM pos_products WHERE organization_id = :o"), {"o": org})
            if existing:
                print(f"  ~ ya hay {existing} productos — datos no se resiembran")
                print(f"\nLogin: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
                return

            loc = uuid.uuid4()
            await s.execute(text("""
                INSERT INTO pos_locations (id, organization_id, code, name, status, created_at, updated_at)
                VALUES (:id, :o, 'PRINCIPAL', 'Tienda', 'active', now(), now())
            """), {"id": loc, "o": org})

            cat_ids: dict[str, uuid.UUID] = {}
            for code, name in CATEGORIES:
                cid = uuid.uuid4()
                cat_ids[code] = cid
                await s.execute(text("""
                    INSERT INTO pos_categories (id, organization_id, code, name, sort_order, status, created_at, updated_at)
                    VALUES (:id, :o, :c, :n, 0, 'active', now(), now())
                """), {"id": cid, "o": org, "c": code, "n": name})

            prod_ids: dict[str, uuid.UUID] = {}
            for sku, name, cat, cost, price, stock, minst, _v in PRODUCTS:
                pid = uuid.uuid4()
                prod_ids[sku] = pid
                await s.execute(text("""
                    INSERT INTO pos_products (id, organization_id, category_id, sku, name, product_type,
                        price, cost, tracks_inventory, attributes, status, created_at, updated_at)
                    VALUES (:id, :o, :cat, :sku, :n, 'simple', :p, :c, true, '{}'::jsonb, 'active', now(), now())
                """), {"id": pid, "o": org, "cat": cat_ids[cat], "sku": sku, "n": name, "p": price, "c": cost})
                await s.execute(text("""
                    INSERT INTO pos_inventory (id, organization_id, product_id, location_id, quantity, min_stock, created_at, updated_at)
                    VALUES (:id, :o, :pid, :loc, :q, :m, now(), now())
                """), {"id": uuid.uuid4(), "o": org, "pid": pid, "loc": loc, "q": stock, "m": minst})

            sales = lines = 0
            for day in range(30, 0, -1):
                day_dt = datetime.utcnow() - timedelta(days=day)
                basket = [(sku, name, int(round(v * random.uniform(0.6, 1.4))), price)
                          for sku, name, cat, cost, price, stock, minst, v in PRODUCTS]
                basket = [b for b in basket if b[2] > 0]
                if not basket:
                    continue
                random.shuffle(basket)
                for ci, chunk in enumerate([basket[i::2] for i in range(2)]):
                    if not chunk:
                        continue
                    sale_id = uuid.uuid4()
                    sub = sum(q * p for _, _, q, p in chunk)
                    when = day_dt + timedelta(hours=10 + ci * 4)
                    await s.execute(text("""
                        INSERT INTO pos_sales (id, organization_id, sale_number, location_id, subtotal,
                            discount_amount, tax_amount, total, payment_method, payment_details, status, created_at, updated_at)
                        VALUES (:id, :o, :num, :loc, :sub, 0, 0, :sub, 'cash', '{}'::jsonb, 'completed', :ts, :ts)
                    """), {"id": sale_id, "o": org, "num": f"V-{when:%Y%m%d}-{ci+1}", "loc": loc, "sub": sub, "ts": when})
                    for sku, name, q, p in chunk:
                        await s.execute(text("""
                            INSERT INTO pos_sale_lines (id, sale_id, product_id, product_name, sku, quantity,
                                unit_price, discount, tax_rate, tax_amount, line_total, created_at, updated_at)
                            VALUES (:id, :sid, :pid, :n, :sku, :q, :p, 0, 0, 0, :lt, :ts, :ts)
                        """), {"id": uuid.uuid4(), "sid": sale_id, "pid": prod_ids[sku], "n": name,
                               "sku": sku, "q": q, "p": p, "lt": q * p, "ts": when})
                        lines += 1
                    sales += 1
            print(f"  + datos: {len(PRODUCTS)} productos · {sales} ventas · {lines} líneas")
    print(f"\n✓ Tienda demo lista. Login: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
