"""DDL setup para SavvyHotel — crea tablas, registra la app y aplica RLS.

Idempotente: re-ejecutar es seguro.

Uso: python backend/scripts/setup_hotel_module.py
"""

from __future__ import annotations

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)

from sqlalchemy import text  # noqa: E402

from src.core.database import Base, async_session_factory, engine  # noqa: E402
from src.apps.hotel import models as hotel_models  # noqa: E402,F401  (registra tablas)

HOTEL_TABLES = [
    "hotel_room_types", "hotel_rooms", "hotel_reservations",
    "hotel_folios", "hotel_folio_charges", "hotel_folio_payments",
]

RLS_POLICY = (
    "(organization_id = nullif(current_setting('app.current_org_id', true), '')::uuid "
    "OR current_setting('app.is_platform', true) = 'on')"
)

REGISTRY = [
    """
    INSERT INTO app_registry (id, code, name, description, icon, color, is_active)
    VALUES (gen_random_uuid(), 'hotel', 'SavvyHotel',
            'PMS para hoteles y hostales: habitaciones, reservas, disponibilidad, folio, housekeeping.',
            'bed', '#0EA5E9', TRUE)
    ON CONFLICT (code) DO UPDATE
      SET name = EXCLUDED.name, description = EXCLUDED.description,
          icon = EXCLUDED.icon, color = EXCLUDED.color, is_active = TRUE
    """,
    """
    INSERT INTO business_type_catalog (code, name, description, default_app_code, icon, color, sort_order, is_active)
    VALUES ('hotel', 'Hotel / Hostal',
            'Gestión hotelera: habitaciones, reservas, check-in/out, folio y housekeeping',
            'hotel', 'bed', '#0EA5E9', 110, TRUE)
    ON CONFLICT (code) DO UPDATE
      SET name = EXCLUDED.name, description = EXCLUDED.description,
          default_app_code = EXCLUDED.default_app_code, icon = EXCLUDED.icon,
          color = EXCLUDED.color, is_active = TRUE
    """,
]


async def main() -> None:
    print("=" * 70)
    print("SavvyHotel · setup del módulo (tablas + registro + RLS)")
    print("=" * 70)

    # 1) Tablas (create_all solo de las de hotel)
    tables = [Base.metadata.tables[t] for t in HOTEL_TABLES]
    async with engine.begin() as conn:
        await conn.run_sync(lambda c: Base.metadata.create_all(c, tables=tables, checkfirst=True))
    print(f"  ✓ {len(tables)} tablas creadas/verificadas")

    # 2) Registro de app + tipo de negocio, RLS y grants
    async with async_session_factory() as s:
        for stmt in REGISTRY:
            await s.execute(text(stmt))
        for t in HOTEL_TABLES:
            await s.execute(text(f"ALTER TABLE {t} ENABLE ROW LEVEL SECURITY"))
            await s.execute(text(f"DROP POLICY IF EXISTS tenant_isolation ON {t}"))
            await s.execute(text(
                f"CREATE POLICY tenant_isolation ON {t} "
                f"USING {RLS_POLICY} WITH CHECK {RLS_POLICY}"))
            # Grant al rol no-propietario (por si default privileges no aplicó).
            await s.execute(text(
                f"GRANT SELECT, INSERT, UPDATE, DELETE ON {t} TO savvy_app"))
        await s.commit()
    print("  ✓ app 'hotel' registrada + tipo de negocio + RLS en 6 tablas")
    print("\n✓ SavvyHotel listo. Actívalo para una org desde el panel de apps.")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
