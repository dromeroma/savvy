"""Helper: códigos de las apps ACTIVAS de una organización.

Las métricas (briefing, insights) deben mostrar SOLO datos de las apps que la
organización tiene activas — nunca de apps que no usa.
"""

from __future__ import annotations

import uuid

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def active_app_codes(db: AsyncSession, org_id: uuid.UUID) -> set[str]:
    rows = (await db.execute(text("""
        SELECT ar.code
        FROM organization_apps oa
        JOIN app_registry ar ON ar.id = oa.app_id
        WHERE oa.organization_id = :org AND oa.status = 'active'
    """), {"org": org_id})).fetchall()
    return {r[0] for r in rows}
