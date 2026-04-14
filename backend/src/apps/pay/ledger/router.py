"""SavvyPay ledger REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.pay.ledger.schemas import *
from src.apps.pay.ledger.service import LedgerEngine

router = APIRouter(
    prefix="/ledger",
    tags=["Pay Ledger"],
    dependencies=[Depends(require_permission("pay", "ledger.write", "reports.view"))],
)

@router.get("/accounts", response_model=list[AccountResponse])
async def list_accounts(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LedgerEngine.list_accounts(db, org_id)

@router.post("/accounts", response_model=AccountResponse, status_code=status.HTTP_201_CREATED)
async def create_account(data: AccountCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LedgerEngine.create_account(db, org_id, data)

@router.get("/balances", response_model=list[AccountBalanceResponse])
async def get_balances(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LedgerEngine.get_all_balances(db, org_id)

@router.post("/journal", response_model=list[LedgerEntryResponse], status_code=status.HTTP_201_CREATED)
async def post_journal(data: JournalCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LedgerEngine.post_journal(db, org_id, data)

@router.get("/entries", response_model=list[LedgerEntryResponse])
async def list_entries(account_id: uuid.UUID | None = Query(None), journal_id: uuid.UUID | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LedgerEngine.list_ledger_entries(db, org_id, account_id, journal_id)

@router.get("/events", response_model=list[EventResponse])
async def list_events(entity_type: str | None = Query(None), entity_id: uuid.UUID | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LedgerEngine.list_events(db, org_id, entity_type, entity_id)
