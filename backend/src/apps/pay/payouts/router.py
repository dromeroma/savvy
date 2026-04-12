"""SavvyPay payouts REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.pay.payouts.schemas import PayoutCreate, PayoutResponse
from src.apps.pay.payouts.service import PayoutService

router = APIRouter(prefix="/payouts", tags=["Pay Payouts"])

@router.get("", response_model=list[PayoutResponse])
async def list_payouts(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PayoutService.list_payouts(db, org_id)

@router.post("", response_model=PayoutResponse, status_code=status.HTTP_201_CREATED)
async def create_payout(data: PayoutCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PayoutService.create_payout(db, org_id, data)
