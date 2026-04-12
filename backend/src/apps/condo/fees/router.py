"""Condo fees REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.condo.fees.schemas import FeeGenerate, FeePayment, FeeResponse
from src.apps.condo.fees.service import FeeService

router = APIRouter(prefix="/fees", tags=["Condo Fees"])

@router.get("", response_model=list[FeeResponse])
async def list_fees(unit_id: uuid.UUID | None = Query(None), period: str | None = Query(None), status_filter: str | None = Query(None, alias="status"), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await FeeService.list_fees(db, org_id, unit_id, period, status_filter)

@router.post("/generate", response_model=list[FeeResponse], status_code=status.HTTP_201_CREATED)
async def generate_fees(data: FeeGenerate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await FeeService.generate_fees(db, org_id, data)

@router.post("/{fee_id}/pay", response_model=FeeResponse)
async def pay_fee(fee_id: uuid.UUID, data: FeePayment, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await FeeService.pay_fee(db, org_id, fee_id, data.amount)
