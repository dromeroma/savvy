"""SavvyEdu student REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.edu.students.schemas import (
    GuardianCreate,
    GuardianResponse,
    StudentCreate,
    StudentListParams,
    StudentResponse,
    StudentUpdate,
)
from src.apps.edu.students.service import StudentService

router = APIRouter(prefix="/students", tags=["Edu Students"])


@router.get("", response_model=dict)
async def list_students(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    search: str | None = Query(None),
    program_id: uuid.UUID | None = Query(None),
    academic_status: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Any:
    params = StudentListParams(
        search=search,
        program_id=program_id,
        academic_status=academic_status,
        page=page,
        page_size=page_size,
    )
    items, total = await StudentService.list_students(db, org_id, params)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_student(
    data: StudentCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await StudentService.create_student(db, org_id, data)


@router.get("/{student_id}", response_model=StudentResponse)
async def get_student(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await StudentService.get_student(db, org_id, student_id)


@router.patch("/{student_id}", response_model=StudentResponse)
async def update_student(
    student_id: uuid.UUID,
    data: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await StudentService.update_student(db, org_id, student_id, data)


# ---------------------------------------------------------------------------
# Guardians
# ---------------------------------------------------------------------------


@router.get("/{student_id}/guardians", response_model=list[GuardianResponse])
async def list_guardians(
    student_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await StudentService.list_guardians(db, org_id, student_id)


@router.post(
    "/{student_id}/guardians",
    response_model=GuardianResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_guardian(
    student_id: uuid.UUID,
    data: GuardianCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await StudentService.add_guardian(db, org_id, student_id, data)


@router.delete("/{student_id}/guardians/{guardian_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_guardian(
    guardian_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await StudentService.remove_guardian(db, org_id, guardian_id)
