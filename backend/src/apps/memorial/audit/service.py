"""Helper para registrar entradas en memorial_audit_log + endpoints de consulta."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.models import MemorialAuditLog


async def record_audit(
    db: AsyncSession,
    *,
    org_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
) -> MemorialAuditLog:
    """Crea una fila en memorial_audit_log. No falla la operación principal
    si el caller no quiere bloquear: úsese siempre dentro de la misma sesión
    que la mutación auditada para que ambas hagan commit en conjunto."""
    entry = MemorialAuditLog(
        organization_id=org_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip_address,
        user_agent=user_agent,
    )
    db.add(entry)
    await db.flush()
    return entry


class AuditService:

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID,
        *,
        resource_type: str | None = None,
        resource_id: uuid.UUID | None = None,
        action: str | None = None,
        actor_user_id: uuid.UUID | None = None,
        date_from: datetime | None = None,
        date_to: datetime | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[MemorialAuditLog]:
        stmt = (
            select(MemorialAuditLog)
            .where(MemorialAuditLog.organization_id == org_id)
            .order_by(MemorialAuditLog.created_at.desc())
            .limit(limit).offset(offset)
        )
        if resource_type:
            stmt = stmt.where(MemorialAuditLog.resource_type == resource_type)
        if resource_id:
            stmt = stmt.where(MemorialAuditLog.resource_id == resource_id)
        if action:
            stmt = stmt.where(MemorialAuditLog.action == action)
        if actor_user_id:
            stmt = stmt.where(MemorialAuditLog.actor_user_id == actor_user_id)
        if date_from:
            stmt = stmt.where(MemorialAuditLog.created_at >= date_from)
        if date_to:
            stmt = stmt.where(MemorialAuditLog.created_at <= date_to)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())
