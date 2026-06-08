"""Contexto de tenant por request + helper para activar la RLS por GUC.

Las políticas RLS (`tenant_isolation`) usan dos GUCs de sesión:
  - app.current_org_id : la organización del request
  - app.is_platform    : 'on' para accesos de plataforma/sistema (cross-org)

Mientras la app se conecte con el rol PROPIETARIO, la RLS se bypassa y estos
GUCs no tienen efecto (defensa dormante). El cut-over a un rol NO propietario
activa la RLS y entonces este contexto se vuelve la frontera real entre tenants.
"""

from __future__ import annotations

import uuid
from contextvars import ContextVar

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

# Contexto por request (lo setea TenantMiddleware).
current_org: ContextVar[uuid.UUID | None] = ContextVar("current_org", default=None)
current_is_platform: ContextVar[bool] = ContextVar("current_is_platform", default=False)


async def apply_tenant_guc(
    session: AsyncSession,
    org_id: uuid.UUID | None,
    *,
    is_platform: bool = False,
) -> None:
    """Activa los GUCs de RLS en la transacción actual de la sesión.

    Usa `set_config(..., is_local => true)` para que aplique a la transacción
    (compatible con PgBouncer en modo transacción). Se debe llamar al inicio de
    cada transacción tras el cut-over al rol no propietario.
    """
    await session.execute(
        text("SELECT set_config('app.current_org_id', :org, true), "
             "set_config('app.is_platform', :plat, true)"),
        {"org": str(org_id) if org_id else "", "plat": "on" if is_platform else "off"},
    )
