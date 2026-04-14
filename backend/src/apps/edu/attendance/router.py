"""SavvyEdu attendance REST endpoints."""

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.edu.attendance.schemas import (
    AttendanceResponse,
    AttendanceSummary,
    BulkAttendanceCreate,
)
from src.apps.edu.attendance.service import AttendanceService

router = APIRouter(
    prefix="/attendance",
    tags=["Edu Attendance"],
    dependencies=[Depends(require_permission("edu", "attendance.write", "students.read"))],
)


@router.post("/bulk", response_model=list[AttendanceResponse], status_code=status.HTTP_201_CREATED)
async def record_bulk_attendance(
    data: BulkAttendanceCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AttendanceService.record_bulk(db, org_id, data)


@router.get("", response_model=list[AttendanceResponse])
async def list_attendance(
    section_id: uuid.UUID = Query(...),
    date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AttendanceService.list_by_section_date(db, org_id, section_id, date)


@router.get("/summary/{section_id}", response_model=AttendanceSummary)
async def get_attendance_summary(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AttendanceService.get_summary(db, org_id, section_id)
