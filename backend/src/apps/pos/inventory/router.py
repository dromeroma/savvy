"""POS inventory REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.pos.inventory.schemas import InventoryAdjustment, InventoryResponse, MovementResponse
from src.apps.pos.inventory.service import InventoryService

router = APIRouter(prefix="/inventory", tags=["POS Inventory"])


@router.get(
    "",
    response_model=list[InventoryResponse],
    dependencies=[Depends(require_permission("pos", "inventory.read"))],
)
async def list_inventory(
    location_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InventoryService.list_inventory(db, org_id, location_id)


@router.post(
    "/adjust",
    response_model=MovementResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("pos", "inventory.write"))],
)
async def adjust_stock(
    data: InventoryAdjustment,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InventoryService.record_movement(db, org_id, data, reference_type="adjustment")


@router.get(
    "/movements",
    response_model=list[MovementResponse],
    dependencies=[Depends(require_permission("pos", "inventory.read"))],
)
async def list_movements(
    product_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InventoryService.list_movements(db, org_id, product_id)
