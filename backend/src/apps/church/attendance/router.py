"""Church attendance REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.church.attendance.schemas import (
    AttendanceBulkCreate,
    AttendanceResponse,
    AttendanceSummary,
)
from src.apps.church.attendance.service import AttendanceService

router = APIRouter(
    prefix="/attendance",
    tags=["Church Attendance"],
    dependencies=[Depends(require_permission("church", "events.manage", "members.read"))],
)


@router.post(
    "/",
    dependencies=[Depends(require_permission("church", "events.manage"))],
)
async def record_attendance(
    data: AttendanceBulkCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Bulk record attendance for an event."""
    count = await AttendanceService.record_attendance(db, org_id, data)
    return {"recorded": count}


@router.get("/event/{event_id}", response_model=list[AttendanceResponse])
async def get_event_attendance(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AttendanceService.get_event_attendance(db, org_id, event_id)


@router.get("/summary", response_model=list[AttendanceSummary])
async def get_attendance_summary(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AttendanceService.get_summary(db, org_id)
