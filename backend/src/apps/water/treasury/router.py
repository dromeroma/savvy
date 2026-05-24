"""Treasury REST endpoints."""

from __future__ import annotations

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.treasury.schemas import (
    ClosingCreate,
    ClosingPreview,
    ClosingResponse,
    MovementCreate,
    MovementListItem,
    MovementResponse,
    TreasuryDashboard,
)
from src.apps.water.treasury.service import TreasuryService
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/treasury", tags=["Water · Tesorería"])


@router.get(
    "/dashboard",
    response_model=TreasuryDashboard,
    dependencies=[Depends(require_permission("water", "treasury.read", "treasury.manage"))],
)
async def get_dashboard(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TreasuryService.dashboard(db, org_id)


# ---------- Movements ----------


@router.get(
    "/movements",
    response_model=list[MovementListItem],
    dependencies=[Depends(require_permission("water", "treasury.read", "treasury.manage"))],
)
async def list_movements(
    cash_account_id: uuid.UUID | None = Query(None),
    type_: str | None = Query(None, alias="type"),
    date_from: date | None = Query(None),
    date_to: date | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TreasuryService.list_movements(
        db, org_id, cash_account_id=cash_account_id, type_=type_,
        date_from=date_from, date_to=date_to, limit=limit, offset=offset,
    )


@router.post(
    "/movements",
    response_model=MovementResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "treasury.manage"))],
)
async def create_movement(
    data: MovementCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await TreasuryService.create_movement(
        db, org_id, data, recorded_by=uuid.UUID(user["sub"]),
    )


@router.delete(
    "/movements/{movement_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("water", "treasury.manage"))],
)
async def delete_movement(
    movement_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await TreasuryService.delete_movement(db, org_id, movement_id)


# ---------- Closings ----------


@router.get(
    "/closings/preview",
    response_model=ClosingPreview,
    dependencies=[Depends(require_permission("water", "treasury.read", "treasury.manage"))],
)
async def closing_preview(
    cash_account_id: uuid.UUID = Query(...),
    closing_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TreasuryService.closing_preview(
        db, org_id, cash_account_id, closing_date,
    )


@router.get(
    "/closings",
    response_model=list[ClosingResponse],
    dependencies=[Depends(require_permission("water", "treasury.read", "treasury.manage"))],
)
async def list_closings(
    cash_account_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TreasuryService.list_closings(db, org_id, cash_account_id, limit)


@router.post(
    "/closings",
    response_model=ClosingResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "treasury.manage"))],
)
async def create_closing(
    data: ClosingCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await TreasuryService.create_closing(
        db, org_id, data, closed_by=uuid.UUID(user["sub"]),
    )
