"""Rotations REST endpoints."""

import uuid
from datetime import date as _date
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.church.rotations.schemas import (
    AssignmentCreate,
    AssignmentResponse,
    AssignmentUpdate,
    RotationCreate,
    RotationResponse,
    RotationUpdate,
)
from src.apps.church.rotations.service import (
    AssignmentService,
    RotationService,
)

router = APIRouter(prefix="/rotations", tags=["Church Rotations"])


# ------------------------------------------------------------------
# Rotations
# ------------------------------------------------------------------

@router.get("", response_model=list[RotationResponse])
async def list_rotations(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RotationService.list_rotations(db, org_id, active_only)


@router.post(
    "",
    response_model=RotationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_rotation(
    data: RotationCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RotationService.create_rotation(db, org_id, data)


@router.get("/{rotation_id}", response_model=RotationResponse)
async def get_rotation(
    rotation_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RotationService.get_rotation(db, org_id, rotation_id)


@router.patch("/{rotation_id}", response_model=RotationResponse)
async def update_rotation(
    rotation_id: uuid.UUID,
    data: RotationUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RotationService.update_rotation(db, org_id, rotation_id, data)


# ------------------------------------------------------------------
# Assignments
# ------------------------------------------------------------------

@router.get("/assignments/list", response_model=list[AssignmentResponse])
async def list_assignments(
    rotation_id: uuid.UUID | None = Query(None),
    person_id: uuid.UUID | None = Query(None),
    from_date: _date | None = Query(None),
    to_date: _date | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AssignmentService.list_assignments(
        db, org_id, rotation_id, person_id, from_date, to_date,
    )


@router.post(
    "/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_assignment(
    data: AssignmentCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AssignmentService.create_assignment(db, org_id, data)


@router.patch(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
)
async def update_assignment(
    assignment_id: uuid.UUID,
    data: AssignmentUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AssignmentService.update_assignment(
        db, org_id, assignment_id, data,
    )
