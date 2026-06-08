"""Genera políticas RLS de aislamiento por tenant en TODAS las tablas con
`organization_id`.

IMPORTANTE / SEGURIDAD:
- La RLS ya está habilitada en las 233 tablas pero SIN políticas. Como la app se
  conecta con el rol propietario (que **bypassa RLS**), estas políticas quedan
  DORMANTES hasta que la app se conecte con un rol NO propietario.
- Aplicar este script es SEGURO: no afecta a la app actual (owner bypassa), solo
  deja la defensa en profundidad lista para el cut-over.

Modelo de política (defensa en profundidad sobre el filtro de aplicación):
  - Acceso normal: organization_id = app.current_org_id (GUC por request).
  - Acceso de plataforma (super-admin / sistema): app.is_platform = 'on'.

Idempotente: DROP POLICY IF EXISTS + CREATE.

Uso:
    python backend/scripts/setup_rls_policies.py            # aplica
    python backend/scripts/setup_rls_policies.py --dry-run  # solo lista
"""

from __future__ import annotations

import argparse
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

POLICY = "tenant_isolation"


async def _org_tables(s) -> list[str]:
    rows = (await s.execute(text("""
        SELECT table_name FROM information_schema.columns
        WHERE table_schema = 'public' AND column_name = 'organization_id'
        ORDER BY table_name
    """))).fetchall()
    return [r[0] for r in rows]


def _policy_sql(table: str) -> list[str]:
    cond = (
        f"(organization_id = nullif(current_setting('app.current_org_id', true), '')::uuid "
        f"OR current_setting('app.is_platform', true) = 'on')"
    )
    return [
        f'ALTER TABLE public."{table}" ENABLE ROW LEVEL SECURITY',
        f'DROP POLICY IF EXISTS {POLICY} ON public."{table}"',
        f'CREATE POLICY {POLICY} ON public."{table}" '
        f'USING {cond} WITH CHECK {cond}',
    ]


async def main(dry: bool) -> None:
    print("=" * 70)
    print("RLS · políticas de aislamiento por tenant (DORMANTES hasta cut-over)")
    print("=" * 70)
    async with async_session_factory() as s:
        tables = await _org_tables(s)
        print(f"Tablas con organization_id: {len(tables)}\n")
        applied = 0
        for t in tables:
            for stmt in _policy_sql(t):
                if not dry:
                    await s.execute(text(stmt))
            applied += 1
            if applied % 30 == 0:
                print(f"  … {applied}/{len(tables)}")
        if not dry:
            await s.commit()
        print(f"\n{'(dry-run) ' if dry else ''}Políticas listas en {applied} tablas.")
        print("Nota: dormantes hasta conectar la app con un rol NO propietario.")
    await engine.dispose()


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    asyncio.run(main(args.dry_run))
