"""Prueba el enforcement de RLS contra DATOS REALES, de forma segura.

No cambia la conexión de la app ni toca el pooler. Desde la conexión owner,
hace `SET ROLE savvy_app` (no propietario → RLS aplica), fija el GUC del org y
verifica que solo ve los datos de ESE org. Luego `RESET ROLE`.

Esto demuestra que las políticas + el GUC funcionan end-to-end antes del flip.

Uso: python backend/scripts/verify_rls.py
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from sqlalchemy import text  # noqa: E402

from src.core.database import async_session_factory, engine  # noqa: E402

ORG_SAN_RAFAEL = "b591b79f-4462-4826-88dc-7e4f706f1d97"  # tiene 8 hr_employees
ORG_ACUEDUCTO = "1fc89791-b383-4fda-a807-672c71a3756b"   # no tiene hr_employees


async def _count_as_role(s, org_id: str | None, *, is_platform: bool = False) -> int:
    async with s.begin():
        await s.execute(text("SET LOCAL ROLE savvy_app"))
        await s.execute(text("SELECT set_config('app.current_org_id', :o, true)"),
                        {"o": org_id or ""})
        await s.execute(text("SELECT set_config('app.is_platform', :p, true)"),
                        {"p": "on" if is_platform else "off"})
        n = await s.scalar(text("SELECT count(*) FROM hr_employees"))
        await s.execute(text("RESET ROLE"))
        return int(n)


async def main() -> None:
    print("=" * 70)
    print("RLS · verificación de enforcement contra datos reales")
    print("=" * 70)
    ok = True
    async with async_session_factory() as s:
        # 1) Como owner (sin SET ROLE): ve todo (RLS bypassada).
        async with s.begin():
            total = int(await s.scalar(text("SELECT count(*) FROM hr_employees")))
        print(f"  owner (sin enforce)           → hr_employees = {total}")

        # 2) Rol savvy_app + GUC San Rafael → debe ver los 8.
        n_sr = await _count_as_role(s, ORG_SAN_RAFAEL)
        print(f"  savvy_app · org=San Rafael    → hr_employees = {n_sr}   (esperado: {total})")
        ok &= n_sr == total

        # 3) Rol savvy_app + GUC Acueducto → debe ver 0 (aislamiento).
        n_ac = await _count_as_role(s, ORG_ACUEDUCTO)
        print(f"  savvy_app · org=Acueducto     → hr_employees = {n_ac}   (esperado: 0)")
        ok &= n_ac == 0

        # 4) Rol savvy_app sin GUC → debe ver 0 (deny por defecto).
        n_none = await _count_as_role(s, None)
        print(f"  savvy_app · sin org           → hr_employees = {n_none}   (esperado: 0)")
        ok &= n_none == 0

        # 5) Rol savvy_app + is_platform=on → ve todo (bypass de plataforma).
        n_plat = await _count_as_role(s, None, is_platform=True)
        print(f"  savvy_app · is_platform=on    → hr_employees = {n_plat}   (esperado: {total})")
        ok &= n_plat == total

    print("\n" + ("✅ RLS AÍSLA CORRECTAMENTE — listo para el flip en staging."
                  if ok else "❌ FALLA: revisar políticas/grants."))
    await engine.dispose()
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    asyncio.run(main())
