"""SavvyEdu enrollment REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.edu.enrollment.schemas import (
    EnrollmentCreate,
    EnrollmentResponse,
    EnrollmentUpdate,
    SectionCreate,
    SectionResponse,
    SectionUpdate,
    WaitlistResponse,
)
from src.apps.edu.enrollment.service import EnrollmentService
from src.apps.edu.enrollment.models import EduEnrollment, EduWaitlist

router = APIRouter(
    prefix="/enrollment",
    tags=["Edu Enrollment"],
    dependencies=[Depends(require_permission("edu", "enrollment.write", "students.read"))],
)


# Sections
@router.get("/sections", response_model=list[SectionResponse])
async def list_sections(
    period_id: uuid.UUID | None = Query(None),
    course_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EnrollmentService.list_sections(db, org_id, period_id, course_id)


@router.post("/sections", response_model=SectionResponse, status_code=status.HTTP_201_CREATED)
async def create_section(
    data: SectionCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EnrollmentService.create_section(db, org_id, data)


@router.get("/sections/{section_id}", response_model=SectionResponse)
async def get_section(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EnrollmentService.get_section(db, org_id, section_id)


@router.patch("/sections/{section_id}", response_model=SectionResponse)
async def update_section(
    section_id: uuid.UUID,
    data: SectionUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EnrollmentService.update_section(db, org_id, section_id, data)


# Enrollments
@router.post("/enroll", status_code=status.HTTP_201_CREATED)
async def enroll_student(
    data: EnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    result = await EnrollmentService.enroll_student(db, org_id, data)
    if isinstance(result, EduWaitlist):
        return {"type": "waitlist", "position": result.position, "id": str(result.id)}
    return {"type": "enrolled", "id": str(result.id)}


@router.get("/sections/{section_id}/students", response_model=list[EnrollmentResponse])
async def list_enrollments(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EnrollmentService.list_enrollments(db, org_id, section_id)


@router.patch("/enrollments/{enrollment_id}", response_model=EnrollmentResponse)
async def update_enrollment(
    enrollment_id: uuid.UUID,
    data: EnrollmentUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EnrollmentService.update_enrollment(db, org_id, enrollment_id, data)


@router.get("/sections/{section_id}/waitlist", response_model=list[WaitlistResponse])
async def list_waitlist(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EnrollmentService.list_waitlist(db, org_id, section_id)
