"""SavvyPay subscriptions REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.pay.subscriptions.schemas import *
from src.apps.pay.subscriptions.service import SubscriptionService

router = APIRouter(
    prefix="/subscriptions",
    tags=["Pay Subscriptions"],
    dependencies=[Depends(require_permission("pay", "subscriptions.write", "subscriptions.read"))],
)

@router.get("/plans", response_model=list[PlanResponse])
async def list_plans(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await SubscriptionService.list_plans(db, org_id)

@router.post("/plans", response_model=PlanResponse, status_code=status.HTTP_201_CREATED)
async def create_plan(data: PlanCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await SubscriptionService.create_plan(db, org_id, data)

@router.get("", response_model=list[SubscriptionResponse])
async def list_subscriptions(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await SubscriptionService.list_subscriptions(db, org_id)

@router.post("", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def subscribe(data: SubscriptionCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await SubscriptionService.subscribe(db, org_id, data)
