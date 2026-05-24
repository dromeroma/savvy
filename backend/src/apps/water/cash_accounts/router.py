"""Cash accounts REST endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.cash_accounts.schemas import (
    CashAccountCreate,
    CashAccountListItem,
    CashAccountResponse,
    CashAccountUpdate,
)
from src.apps.water.cash_accounts.service import CashAccountsService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/cash-accounts", tags=["Water · Tesorería · Cuentas"])


@router.get(
    "",
    response_model=list[CashAccountListItem],
    dependencies=[Depends(require_permission("water", "treasury.read", "treasury.manage", "payments.read"))],
)
async def list_accounts(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CashAccountsService.list_accounts(db, org_id, active_only=active_only)


@router.get(
    "/{account_id}",
    response_model=CashAccountResponse,
    dependencies=[Depends(require_permission("water", "treasury.read", "treasury.manage"))],
)
async def get_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CashAccountsService.get_account(db, org_id, account_id)


@router.post(
    "",
    response_model=CashAccountResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "treasury.manage"))],
)
async def create_account(
    data: CashAccountCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CashAccountsService.create_account(db, org_id, data)


@router.patch(
    "/{account_id}",
    response_model=CashAccountResponse,
    dependencies=[Depends(require_permission("water", "treasury.manage"))],
)
async def update_account(
    account_id: uuid.UUID,
    data: CashAccountUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CashAccountsService.update_account(db, org_id, account_id, data)


@router.delete(
    "/{account_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("water", "treasury.manage"))],
)
async def delete_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await CashAccountsService.delete_account(db, org_id, account_id)
