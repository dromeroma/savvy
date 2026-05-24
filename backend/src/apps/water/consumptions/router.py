"""Consumptions REST endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.consumptions.schemas import (
    ConsumptionCreate,
    ConsumptionListItem,
    ConsumptionResponse,
    ConsumptionUpdate,
)
from src.apps.water.consumptions.service import ConsumptionsService
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/consumptions", tags=["Water · Lecturas"])


@router.get(
    "",
    response_model=list[ConsumptionListItem],
    dependencies=[Depends(require_permission("water", "consumptions.read", "consumptions.manage"))],
)
async def list_consumptions(
    period_year: int | None = Query(None),
    period_month: int | None = Query(None, ge=1, le=12),
    meter_id: uuid.UUID | None = Query(None),
    subscriber_id: uuid.UUID | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ConsumptionsService.list_consumptions(
        db, org_id, period_year=period_year, period_month=period_month,
        meter_id=meter_id, subscriber_id=subscriber_id,
        limit=limit, offset=offset,
    )


@router.get(
    "/{cons_id}",
    response_model=ConsumptionResponse,
    dependencies=[Depends(require_permission("water", "consumptions.read", "consumptions.manage"))],
)
async def get_consumption(
    cons_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ConsumptionsService.get_consumption(db, org_id, cons_id)


@router.post(
    "",
    response_model=ConsumptionResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "consumptions.manage"))],
)
async def create_consumption(
    data: ConsumptionCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await ConsumptionsService.create_consumption(
        db, org_id, data, recorded_by=uuid.UUID(user["sub"]),
    )


@router.patch(
    "/{cons_id}",
    response_model=ConsumptionResponse,
    dependencies=[Depends(require_permission("water", "consumptions.manage"))],
)
async def update_consumption(
    cons_id: uuid.UUID,
    data: ConsumptionUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ConsumptionsService.update_consumption(db, org_id, cons_id, data)


@router.delete(
    "/{cons_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("water", "consumptions.manage"))],
)
async def delete_consumption(
    cons_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await ConsumptionsService.delete_consumption(db, org_id, cons_id)
