"""SavvyEdu teacher REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.edu.teachers.schemas import (
    TeacherCreate,
    TeacherListParams,
    TeacherResponse,
    TeacherUpdate,
)
from src.apps.edu.teachers.service import TeacherService

router = APIRouter(
    prefix="/teachers",
    tags=["Edu Teachers"],
    dependencies=[Depends(require_permission("edu", "students.read", "students.write"))],
)


@router.get("", response_model=dict)
async def list_teachers(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    search: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    department_scope_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Any:
    params = TeacherListParams(
        search=search,
        status=status_filter,
        department_scope_id=department_scope_id,
        page=page,
        page_size=page_size,
    )
    items, total = await TeacherService.list_teachers(db, org_id, params)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher(
    data: TeacherCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TeacherService.create_teacher(db, org_id, data)


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_teacher(
    teacher_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TeacherService.get_teacher(db, org_id, teacher_id)


@router.patch("/{teacher_id}", response_model=TeacherResponse)
async def update_teacher(
    teacher_id: uuid.UUID,
    data: TeacherUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TeacherService.update_teacher(db, org_id, teacher_id, data)
