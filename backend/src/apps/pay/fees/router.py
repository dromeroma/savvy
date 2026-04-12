"""SavvyPay fees REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.pay.fees.schemas import FeeRuleCreate, FeeRuleResponse
from src.apps.pay.fees.service import FeeService

router = APIRouter(prefix="/fees", tags=["Pay Fees"])

@router.get("/rules", response_model=list[FeeRuleResponse])
async def list_rules(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await FeeService.list_rules(db, org_id)

@router.post("/rules", response_model=FeeRuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(data: FeeRuleCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await FeeService.create_rule(db, org_id, data)

@router.get("/calculate")
async def calculate_fee(amount: float = Query(..., gt=0), tx_type: str = Query("payment"), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    fee = await FeeService.calculate_fee(db, org_id, amount, tx_type)
    return {"amount": amount, "fee": float(fee), "net": amount - float(fee)}
