"""POS sales REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.pos.sales.schemas import SaleCreate, SaleResponse
from src.apps.pos.sales.service import SalesService

router = APIRouter(prefix="/sales", tags=["POS Sales"])


@router.get(
    "",
    response_model=list[SaleResponse],
    dependencies=[Depends(require_permission("pos", "reports.view", "sales.create"))],
)
async def list_sales(
    location_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SalesService.list_sales(db, org_id, location_id, status_filter)


@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("pos", "sales.create"))],
)
async def create_sale(
    data: SaleCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SalesService.create_sale(db, org_id, data)


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    dependencies=[Depends(require_permission("pos", "reports.view", "sales.create"))],
)
async def get_sale(
    sale_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SalesService.get_sale(db, org_id, sale_id)


@router.post(
    "/{sale_id}/void",
    response_model=SaleResponse,
    dependencies=[Depends(require_permission("pos", "sales.void"))],
)
async def void_sale(
    sale_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SalesService.void_sale(db, org_id, sale_id)
