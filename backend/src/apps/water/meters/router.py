"""Water meters REST endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.meters.schemas import (
    MeterCreate,
    MeterListItem,
    MeterResponse,
    MeterUpdate,
)
from src.apps.water.meters.service import MetersService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(
    prefix="/meters",
    tags=["Water · Medidores"],
)


@router.get(
    "",
    response_model=list[MeterListItem],
    dependencies=[Depends(require_permission("water", "meters.read", "meters.manage"))],
)
async def list_meters(
    search: str | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    subscriber_id: uuid.UUID | None = Query(None),
    unassigned_only: bool = Query(False),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await MetersService.list_meters(
        db, org_id, search=search, status=status_,
        subscriber_id=subscriber_id, unassigned_only=unassigned_only,
        limit=limit, offset=offset,
    )


@router.get(
    "/{meter_id}",
    response_model=MeterResponse,
    dependencies=[Depends(require_permission("water", "meters.read", "meters.manage"))],
)
async def get_meter(
    meter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await MetersService.get_meter(db, org_id, meter_id)


@router.post(
    "",
    response_model=MeterResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "meters.manage"))],
)
async def create_meter(
    data: MeterCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await MetersService.create_meter(db, org_id, data)


@router.patch(
    "/{meter_id}",
    response_model=MeterResponse,
    dependencies=[Depends(require_permission("water", "meters.manage"))],
)
async def update_meter(
    meter_id: uuid.UUID,
    data: MeterUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await MetersService.update_meter(db, org_id, meter_id, data)


@router.delete(
    "/{meter_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("water", "meters.manage"))],
)
async def delete_meter(
    meter_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await MetersService.delete_meter(db, org_id, meter_id)
