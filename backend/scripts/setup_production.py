"""One-shot: prepara la base de datos para el enforcement de RLS, en orden.

Corre, de forma idempotente y en secuencia:
  1. setup_rls_policies.py  → políticas tenant_isolation en todas las tablas
  2. setup_rls_role.py      → rol no-propietario savvy_app + grants
  3. verify_rls.py          → PRUEBA que la RLS aísla (sale != 0 si falla)

Pensado para correr contra una BD nueva (o el branch de staging) antes de
poner SAVVY_RLS_ENFORCE=true. NO activa el flag — eso es decisión de despliegue.

Uso: python backend/scripts/setup_production.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


async def main() -> None:
    print("#" * 70)
    print("# Savvy · preparación de RLS para producción/staging")
    print("#" * 70)

    # 1) Políticas
    print("\n[1/3] Políticas tenant_isolation …")
    from scripts import setup_rls_policies
    await setup_rls_policies.main(False)  # dry=False

    # 2) Rol + grants
    print("\n[2/3] Rol savvy_app + grants …")
    from scripts import setup_rls_role
    await setup_rls_role.main()

    # 3) Verificación (sale con código !=0 si la RLS no aísla)
    print("\n[3/3] Verificación de aislamiento …")
    from scripts import verify_rls
    try:
        await verify_rls.main()
    except SystemExit as exc:
        if exc.code:
            print("\n❌ La verificación de RLS FALLÓ. NO actives SAVVY_RLS_ENFORCE.")
            raise
    print("\n" + "=" * 70)
    print("✅ Listo. La BD está preparada. Para activar: SAVVY_RLS_ENFORCE=true")
    print("   (primero en staging + smoke; rollback = volver a false).")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
