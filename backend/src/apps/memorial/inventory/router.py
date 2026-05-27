"""Endpoints REST de inventario."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.inventory.schemas import (
    ItemCreate,
    ItemListItem,
    ItemResponse,
    ItemUpdate,
    MovementCreate,
    MovementListItem,
    MovementResponse,
)
from src.apps.memorial.inventory.service import InventoryService
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/inventory", tags=["Memorial · Inventario"])


def _user_uuid(user: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(user["sub"])


# Items


@router.get(
    "/items",
    response_model=list[ItemListItem],
    dependencies=[Depends(require_permission(
        "memorial", "inventory.read", "inventory.manage",
    ))],
)
async def list_items(
    category: str | None = Query(None),
    active_only: bool = Query(False),
    low_stock_only: bool = Query(False),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InventoryService.list_items(
        db, org_id, category=category, active_only=active_only,
        low_stock_only=low_stock_only, search=search,
    )


@router.get(
    "/items/{item_id}",
    response_model=ItemResponse,
    dependencies=[Depends(require_permission(
        "memorial", "inventory.read", "inventory.manage",
    ))],
)
async def get_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InventoryService.get_item(db, org_id, item_id)


@router.post(
    "/items",
    response_model=ItemResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "inventory.manage"))],
)
async def create_item(
    data: ItemCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await InventoryService.create_item(db, org_id, data, _user_uuid(user))


@router.patch(
    "/items/{item_id}",
    response_model=ItemResponse,
    dependencies=[Depends(require_permission("memorial", "inventory.manage"))],
)
async def update_item(
    item_id: uuid.UUID,
    data: ItemUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InventoryService.update_item(db, org_id, item_id, data)


@router.delete(
    "/items/{item_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("memorial", "inventory.manage"))],
)
async def delete_item(
    item_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await InventoryService.delete_item(db, org_id, item_id)


# Movements


@router.get(
    "/movements",
    response_model=list[MovementListItem],
    dependencies=[Depends(require_permission(
        "memorial", "inventory.read", "inventory.manage",
    ))],
)
async def list_movements(
    item_id: uuid.UUID | None = Query(None),
    movement_type: str | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InventoryService.list_movements(
        db, org_id, item_id=item_id, movement_type=movement_type,
        date_from=date_from, date_to=date_to,
        limit=limit, offset=offset,
    )


@router.post(
    "/movements",
    response_model=MovementResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "inventory.manage"))],
)
async def record_movement(
    data: MovementCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await InventoryService.record_movement(db, org_id, data, _user_uuid(user))
