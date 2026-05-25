"""PQRS admin REST endpoints.

Customer endpoints live in /water/portal/* — see water.portal.router.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.pqrs.schemas import (
    AdminPqrsCreate,
    PqrsListItem,
    PqrsRespond,
    PqrsResponse,
    PqrsStatusUpdate,
)
from src.apps.water.pqrs.service import PqrsService
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/pqrs", tags=["Water · PQRS"])


@router.get(
    "",
    response_model=list[PqrsListItem],
    dependencies=[Depends(require_permission("water", "pqrs.read", "pqrs.manage"))],
)
async def list_pqrs(
    status_: str | None = Query(None, alias="status"),
    type_: str | None = Query(None, alias="type"),
    subscriber_id: uuid.UUID | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PqrsService.list_pqrs(
        db, org_id, status_=status_, type_=type_,
        subscriber_id=subscriber_id, limit=limit, offset=offset,
    )


@router.get(
    "/{pqrs_id}",
    response_model=PqrsResponse,
    dependencies=[Depends(require_permission("water", "pqrs.read", "pqrs.manage"))],
)
async def get_pqrs(
    pqrs_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PqrsService.get_pqrs(db, org_id, pqrs_id)


@router.post(
    "",
    response_model=PqrsResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "pqrs.manage"))],
)
async def create_pqrs(
    data: AdminPqrsCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PqrsService.create_pqrs(
        db, org_id, data.subscriber_id, data, created_by=uuid.UUID(user["sub"]),
    )


@router.post(
    "/{pqrs_id}/respond",
    response_model=PqrsResponse,
    dependencies=[Depends(require_permission("water", "pqrs.manage"))],
)
async def respond_pqrs(
    pqrs_id: uuid.UUID,
    data: PqrsRespond,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PqrsService.respond_pqrs(
        db, org_id, pqrs_id, data, responded_by=uuid.UUID(user["sub"]),
    )


@router.patch(
    "/{pqrs_id}/status",
    response_model=PqrsResponse,
    dependencies=[Depends(require_permission("water", "pqrs.manage"))],
)
async def update_status(
    pqrs_id: uuid.UUID,
    data: PqrsStatusUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PqrsService.update_status(db, org_id, pqrs_id, data)
