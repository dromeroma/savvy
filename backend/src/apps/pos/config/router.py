"""POS config REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.pos.config.schemas import *
from src.apps.pos.config.service import ConfigService

router = APIRouter(prefix="/config", tags=["POS Config"])


@router.get(
    "/taxes",
    response_model=list[TaxResponse],
    dependencies=[Depends(require_permission("pos", "sales.create", "products.manage"))],
)
async def list_taxes(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ConfigService.list_taxes(db, org_id)


@router.post(
    "/taxes",
    response_model=TaxResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("pos", "products.manage"))],
)
async def create_tax(
    data: TaxCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ConfigService.create_tax(db, org_id, data)


@router.get(
    "/discounts",
    response_model=list[DiscountResponse],
    dependencies=[Depends(require_permission("pos", "sales.create", "discounts.apply"))],
)
async def list_discounts(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ConfigService.list_discounts(db, org_id)


@router.post(
    "/discounts",
    response_model=DiscountResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("pos", "products.manage"))],
)
async def create_discount(
    data: DiscountCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ConfigService.create_discount(db, org_id, data)
