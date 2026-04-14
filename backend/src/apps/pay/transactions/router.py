"""SavvyPay transactions REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.pay.transactions.schemas import *
from src.apps.pay.transactions.service import TransactionService

router = APIRouter(
    prefix="/transactions",
    tags=["Pay Transactions"],
    dependencies=[Depends(require_permission("pay", "transactions.write", "transactions.read"))],
)

@router.get("", response_model=list[TransactionResponse])
async def list_transactions(status_filter: str | None = Query(None, alias="status"), tx_type: str | None = Query(None, alias="type"), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await TransactionService.list_transactions(db, org_id, status_filter, tx_type)

@router.post("", response_model=TransactionResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(data: TransactionCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await TransactionService.create_transaction(db, org_id, data)

@router.get("/{tx_id}", response_model=TransactionResponse)
async def get_transaction(tx_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await TransactionService.get_transaction(db, org_id, tx_id)

@router.post("/{tx_id}/transition", response_model=TransactionResponse)
async def transition_transaction(tx_id: uuid.UUID, data: TransactionAction, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await TransactionService.transition(db, org_id, tx_id, data)

@router.post("/refunds", response_model=RefundResponse, status_code=status.HTTP_201_CREATED)
async def create_refund(data: RefundCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await TransactionService.create_refund(db, org_id, data)
