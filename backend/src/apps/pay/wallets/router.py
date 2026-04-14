"""SavvyPay wallets REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.pay.wallets.schemas import *
from src.apps.pay.wallets.service import WalletService

router = APIRouter(
    prefix="/wallets",
    tags=["Pay Wallets"],
    dependencies=[Depends(require_permission("pay", "wallets.write", "wallets.read"))],
)

@router.get("", response_model=list[WalletResponse])
async def list_wallets(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await WalletService.list_wallets(db, org_id)

@router.post("", response_model=WalletResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(data: WalletCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await WalletService.create_wallet(db, org_id, data)

@router.get("/{wallet_id}/balance", response_model=WalletBalanceResponse)
async def get_balance(wallet_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await WalletService.get_balance(db, org_id, wallet_id)

@router.post("/{wallet_id}/fund", response_model=WalletBalanceResponse)
async def fund_wallet(wallet_id: uuid.UUID, data: WalletFund, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await WalletService.fund_wallet(db, org_id, wallet_id, data)

@router.post("/{wallet_id}/transfer", response_model=WalletBalanceResponse)
async def transfer(wallet_id: uuid.UUID, data: WalletTransfer, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await WalletService.transfer(db, org_id, wallet_id, data)
