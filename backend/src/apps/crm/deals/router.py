"""CRM deals REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.crm.deals.schemas import DealCreate, DealResponse, DealUpdate, StageHistoryResponse
from src.apps.crm.deals.service import DealService

router = APIRouter(
    prefix="/deals",
    tags=["CRM Deals"],
    dependencies=[Depends(require_permission("crm", "deals.write", "reports.view"))],
)
_WRITE = [Depends(require_permission("crm", "deals.write"))]

@router.get("", response_model=list[DealResponse])
async def list_deals(
    pipeline_id: uuid.UUID | None = Query(None), status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DealService.list_deals(db, org_id, pipeline_id, status_filter)

@router.post("", response_model=DealResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_deal(data: DealCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await DealService.create_deal(db, org_id, data)

@router.get("/{deal_id}", response_model=DealResponse)
async def get_deal(deal_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await DealService.get_deal(db, org_id, deal_id)

@router.patch("/{deal_id}", response_model=DealResponse, dependencies=_WRITE)
async def update_deal(deal_id: uuid.UUID, data: DealUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await DealService.update_deal(db, org_id, deal_id, data)

@router.get("/{deal_id}/history", response_model=list[StageHistoryResponse])
async def get_stage_history(deal_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await DealService.get_stage_history(db, deal_id)
