"""Crea el rol NO propietario `savvy_app` para el enforcement de RLS.

La app, al activar SAVVY_RLS_ENFORCE, hace `SET LOCAL ROLE savvy_app` por
transacción de tenant → la RLS aplica (el rol no es propietario ni BYPASSRLS).
El rol es NOLOGIN (no necesita credenciales: se entra vía SET ROLE desde la
conexión owner existente, que ya funciona con el pooler de Supabase).

Idempotente. Otorga DML sobre tablas + uso de secuencias, presente y futuro.

Uso: python backend/scripts/setup_rls_role.py
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

from src.core.database import async_session_factory, engine  # noqa: E402

ROLE = "savvy_app"

DDL = [
    # Crear el rol si no existe (NOLOGIN, sin bypass de RLS).
    f"""
    DO $$
    BEGIN
        IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '{ROLE}') THEN
            CREATE ROLE {ROLE} NOLOGIN NOBYPASSRLS;
        END IF;
    END $$
    """,
    # El rol conectado (la app) debe ser miembro de {ROLE} para poder SET ROLE.
    f"DO $$ BEGIN EXECUTE format('GRANT {ROLE} TO %I', current_user); END $$",
    f"GRANT USAGE ON SCHEMA public TO {ROLE}",
    f"GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {ROLE}",
    f"GRANT USAGE, SELECT, UPDATE ON ALL SEQUENCES IN SCHEMA public TO {ROLE}",
    # Privilegios por defecto para tablas/secuencias futuras.
    f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO {ROLE}",
    f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT USAGE, SELECT, UPDATE ON SEQUENCES TO {ROLE}",
]


async def main() -> None:
    print("=" * 70)
    print(f"RLS · creando rol no-propietario '{ROLE}' + grants")
    print("=" * 70)
    async with async_session_factory() as s:
        for i, stmt in enumerate(DDL, 1):
            print(f"  [{i}/{len(DDL)}] {' '.join(stmt.split())[:80]}")
            await s.execute(text(stmt))
        await s.commit()
    print(f"\nOK — rol '{ROLE}' listo. Activar con SAVVY_RLS_ENFORCE=true (en staging primero).")
    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
