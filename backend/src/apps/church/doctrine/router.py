"""Doctrine REST endpoints."""

import uuid
from datetime import date as _date
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.church.doctrine.schemas import (
    DoctrineAttendanceBulkCreate,
    DoctrineAttendanceCreate,
    DoctrineAttendanceResponse,
    DoctrineGroupCreate,
    DoctrineGroupResponse,
    DoctrineGroupUpdate,
    EnrollmentCreate,
    EnrollmentResponse,
    EnrollmentUpdate,
)
from src.apps.church.doctrine.service import (
    DoctrineAttendanceService,
    DoctrineGroupService,
    EnrollmentService,
)

router = APIRouter(
    prefix="/doctrine",
    tags=["Church Doctrine"],
    dependencies=[Depends(require_permission("church", "doctrine.manage", "members.read"))],
)


# ------------------------------------------------------------------
# Groups
# ------------------------------------------------------------------

@router.get("/groups", response_model=list[DoctrineGroupResponse])
async def list_groups(
    status_filter: str | None = Query(None, alias="status"),
    scope_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DoctrineGroupService.list_groups(db, org_id, status_filter, scope_id)


@router.post(
    "/groups",
    response_model=DoctrineGroupResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_group(
    data: DoctrineGroupCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DoctrineGroupService.create_group(db, org_id, data)


@router.get("/groups/{group_id}", response_model=DoctrineGroupResponse)
async def get_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DoctrineGroupService.get_group(db, org_id, group_id)


@router.patch("/groups/{group_id}", response_model=DoctrineGroupResponse)
async def update_group(
    group_id: uuid.UUID,
    data: DoctrineGroupUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DoctrineGroupService.update_group(db, org_id, group_id, data)


# ------------------------------------------------------------------
# Enrollments
# ------------------------------------------------------------------

@router.get(
    "/groups/{group_id}/enrollments",
    response_model=list[EnrollmentResponse],
)
async def list_enrollments(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EnrollmentService.list_enrollments(db, org_id, group_id)


@router.post(
    "/enrollments",
    response_model=EnrollmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_enrollment(
    data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EnrollmentService.create_enrollment(db, org_id, data)


@router.patch("/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: uuid.UUID,
    data: EnrollmentUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EnrollmentService.update_enrollment(db, org_id, enrollment_id, data)


# ------------------------------------------------------------------
# Attendance
# ------------------------------------------------------------------

@router.get(
    "/groups/{group_id}/attendance",
    response_model=list[DoctrineAttendanceResponse],
)
async def list_attendance(
    group_id: uuid.UUID,
    session_date: _date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DoctrineAttendanceService.list_attendance(
        db, org_id, group_id, session_date,
    )


@router.post(
    "/attendance",
    response_model=DoctrineAttendanceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_attendance(
    data: DoctrineAttendanceCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DoctrineAttendanceService.create_attendance(db, org_id, data)


@router.post(
    "/attendance/bulk",
    response_model=list[DoctrineAttendanceResponse],
    status_code=status.HTTP_201_CREATED,
)
async def bulk_create_attendance(
    data: DoctrineAttendanceBulkCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DoctrineAttendanceService.bulk_create(db, org_id, data)
