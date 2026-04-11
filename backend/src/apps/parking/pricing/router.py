"""Parking pricing REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.parking.pricing.schemas import *
from src.apps.parking.pricing.service import PricingService

router = APIRouter(prefix="/pricing", tags=["Parking Pricing"])

@router.get("/rules", response_model=list[PricingRuleResponse])
async def list_rules(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PricingService.list_rules(db, org_id)

@router.post("/rules", response_model=PricingRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(data: PricingRuleCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PricingService.create_rule(db, org_id, data)

@router.get("/subscriptions", response_model=list[SubscriptionResponse])
async def list_subscriptions(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PricingService.list_subscriptions(db, org_id)

@router.post("/subscriptions", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(data: SubscriptionCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PricingService.create_subscription(db, org_id, data)
