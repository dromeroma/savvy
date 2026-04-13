"""SavvyCredit products REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.credit.products.schemas import (
    CreditProductCreate,
    CreditProductResponse,
    CreditProductUpdate,
)
from src.apps.credit.products.service import CreditProductService

router = APIRouter(
    prefix="/products",
    tags=["Credit Products"],
    dependencies=[Depends(require_permission("credit", "loans.create", "loans.approve", "reports.view"))],
)
_APPROVE = [Depends(require_permission("credit", "loans.approve"))]


@router.get("", response_model=list[CreditProductResponse])
async def list_products(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CreditProductService.list_products(db, org_id, status_filter)


@router.post("", response_model=CreditProductResponse, status_code=status.HTTP_201_CREATED, dependencies=_APPROVE)
async def create_product(
    data: CreditProductCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CreditProductService.create_product(db, org_id, data)


@router.get("/{product_id}", response_model=CreditProductResponse)
async def get_product(
    product_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CreditProductService.get_product(db, org_id, product_id)


@router.patch("/{product_id}", response_model=CreditProductResponse, dependencies=_APPROVE)
async def update_product(
    product_id: uuid.UUID,
    data: CreditProductUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CreditProductService.update_product(db, org_id, product_id, data)
