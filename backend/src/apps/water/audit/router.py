"""Audit REST endpoint (read-only — entries are appended by other services)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.audit.schemas import AuditEntry
from src.apps.water.audit.service import AuditService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/audit", tags=["Water · Auditoría"])


@router.get(
    "",
    response_model=list[AuditEntry],
    dependencies=[Depends(require_permission("water", "audit.read", "subscribers.manage"))],
)
async def list_audit(
    actor_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    resource_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AuditService.list_entries(
        db, org_id, actor_id=actor_id, action=action,
        resource_type=resource_type, limit=limit,
    )
