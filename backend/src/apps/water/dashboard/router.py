"""Water dashboard endpoint — KPIs for the org."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.models import WaterMeter, WaterSubscriber
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(
    prefix="/dashboard",
    tags=["Water · Dashboard"],
    dependencies=[Depends(require_permission("water", "dashboard.view", "subscribers.read"))],
)


@router.get("/kpis")
async def get_kpis(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    by_status = dict((await db.execute(
        select(WaterSubscriber.status, func.count(WaterSubscriber.id))
        .where(WaterSubscriber.organization_id == org_id)
        .group_by(WaterSubscriber.status)
    )).all())
    total_subscribers = sum(by_status.values()) if by_status else 0

    total_meters = await db.scalar(
        select(func.count(WaterMeter.id)).where(WaterMeter.organization_id == org_id),
    ) or 0
    assigned_meters = await db.scalar(
        select(func.count(WaterMeter.id)).where(
            WaterMeter.organization_id == org_id,
            WaterMeter.subscriber_id.isnot(None),
        ),
    ) or 0

    return {
        "total_subscribers": total_subscribers,
        "by_status": {
            "active": int(by_status.get("active", 0)),
            "suspended": int(by_status.get("suspended", 0)),
            "overdue": int(by_status.get("overdue", 0)),
            "retired": int(by_status.get("retired", 0)),
        },
        "total_meters": int(total_meters),
        "assigned_meters": int(assigned_meters),
        "unassigned_meters": int(total_meters) - int(assigned_meters),
    }
