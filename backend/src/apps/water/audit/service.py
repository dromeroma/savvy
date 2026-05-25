"""Audit service — append + query."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.audit.schemas import AuditEntry
from src.apps.water.models import WaterAuditLog
from src.modules.auth.models import User


async def write_audit(
    db: AsyncSession,
    org_id: uuid.UUID,
    actor_user_id: uuid.UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: uuid.UUID | None = None,
    details: dict[str, Any] | None = None,
    request: Request | None = None,
) -> WaterAuditLog:
    """Append an entry. Producers call this from their service layer."""
    ip = ua = None
    if request is not None:
        ip = request.headers.get("x-forwarded-for") or (
            request.client.host if request.client else None
        )
        ua = request.headers.get("user-agent")
    entry = WaterAuditLog(
        organization_id=org_id,
        actor_user_id=actor_user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        details=details,
        ip_address=ip,
        user_agent=ua,
    )
    db.add(entry)
    await db.flush()
    return entry


class AuditService:

    @staticmethod
    async def list_entries(
        db: AsyncSession,
        org_id: uuid.UUID,
        actor_id: uuid.UUID | None = None,
        action: str | None = None,
        resource_type: str | None = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        stmt = (
            select(
                WaterAuditLog.id, WaterAuditLog.actor_user_id, User.name,
                WaterAuditLog.action, WaterAuditLog.resource_type,
                WaterAuditLog.resource_id, WaterAuditLog.details,
                WaterAuditLog.ip_address, WaterAuditLog.created_at,
            )
            .outerjoin(User, User.id == WaterAuditLog.actor_user_id)
            .where(WaterAuditLog.organization_id == org_id)
            .order_by(WaterAuditLog.created_at.desc())
            .limit(limit)
        )
        if actor_id is not None:
            stmt = stmt.where(WaterAuditLog.actor_user_id == actor_id)
        if action:
            stmt = stmt.where(WaterAuditLog.action == action)
        if resource_type:
            stmt = stmt.where(WaterAuditLog.resource_type == resource_type)

        rows = await db.execute(stmt)
        return [
            AuditEntry(
                id=r[0], actor_user_id=r[1], actor_name=r[2],
                action=r[3], resource_type=r[4], resource_id=r[5],
                details=r[6], ip_address=r[7], created_at=r[8],
            )
            for r in rows.all()
        ]
