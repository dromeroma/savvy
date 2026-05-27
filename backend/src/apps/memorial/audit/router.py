"""Endpoints REST de auditoría — solo lectura."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.audit.schemas import AuditLogEntry
from src.apps.memorial.audit.service import AuditService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/audit", tags=["Memorial · Auditoría"])


def _perm_read():
    return Depends(require_permission(
        "memorial", "audit.read", "reports.manage",
    ))


@router.get("/log", response_model=list[AuditLogEntry], dependencies=[_perm_read()])
async def list_audit(
    resource_type: str | None = Query(None),
    resource_id: uuid.UUID | None = Query(None),
    action: str | None = Query(None),
    actor_user_id: uuid.UUID | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AuditService.list_(
        db, org_id,
        resource_type=resource_type, resource_id=resource_id,
        action=action, actor_user_id=actor_user_id,
        date_from=date_from, date_to=date_to,
        limit=limit, offset=offset,
    )
