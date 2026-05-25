"""Notifications REST endpoints (current user inbox)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.notifications.schemas import (
    MarkReadRequest,
    NotificationItem,
    UnreadCount,
)
from src.apps.water.notifications.service import NotificationsService
from src.core.dependencies import get_current_user, get_db, get_org_id

router = APIRouter(prefix="/notifications", tags=["Water · Notificaciones"])


@router.get("", response_model=list[NotificationItem])
async def list_notifications(
    unread_only: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await NotificationsService.list_for_user(
        db, org_id, uuid.UUID(user["sub"]),
        unread_only=unread_only, limit=limit,
    )


@router.get("/unread-count", response_model=UnreadCount)
async def unread_count(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    n = await NotificationsService.count_unread(db, org_id, uuid.UUID(user["sub"]))
    return {"unread": n}


@router.post(
    "/mark-read",
    status_code=status.HTTP_200_OK,
)
async def mark_read(
    data: MarkReadRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    updated = await NotificationsService.mark_read(
        db, org_id, uuid.UUID(user["sub"]), ids=data.ids or None,
    )
    return {"updated": updated}


@router.post("/mark-all-read")
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    updated = await NotificationsService.mark_read(
        db, org_id, uuid.UUID(user["sub"]), ids=None,
    )
    return {"updated": updated}
