"""FastAPI router for the SavvyFinance module."""

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.finance.schemas import (
    CategoryCreate,
    CategoryResponse,
    PaymentAccountCreate,
    PaymentAccountResponse,
    TransactionCreate,
    TransactionListParams,
    TransactionResponse,
    TransactionSummary,
)
from src.modules.finance.service import FinanceService

router = APIRouter(prefix="/finance", tags=["Finance"])


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@router.get(
    "/categories",
    response_model=list[CategoryResponse],
)
async def list_categories(
    app_code: str | None = Query(default=None),
    type: str | None = Query(default=None, alias="type"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List finance categories with optional filters."""
    return await FinanceService.list_categories(db, org_id, app_code, type)


@router.post(
    "/categories",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_category(
    data: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Create a new finance category."""
    return await FinanceService.create_category(db, org_id, data)


# ---------------------------------------------------------------------------
# Transactions
# ---------------------------------------------------------------------------


@router.get(
    "/transactions/summary",
    response_model=TransactionSummary,
)
async def transaction_summary(
    date_from: date = Query(...),
    date_to: date = Query(...),
    app_code: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Get an aggregated income/expense summary for a date range."""
    return await FinanceService.get_summary(db, org_id, date_from, date_to, app_code)


@router.get(
    "/transactions/{transaction_id}",
    response_model=TransactionResponse,
)
async def get_transaction(
    transaction_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Get a single transaction by ID."""
    return await FinanceService.get_transaction(db, org_id, transaction_id)


@router.get(
    "/transactions",
    response_model=dict,
)
async def list_transactions(
    type: str | None = Query(default=None),
    app_code: str | None = Query(default=None),
    date_from: date | None = Query(default=None),
    date_to: date | None = Query(default=None),
    category_code: str | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List transactions with pagination and filters."""
    params = TransactionListParams(
        type=type,
        app_code=app_code,
        date_from=date_from,
        date_to=date_to,
        category_code=category_code,
        page=page,
        page_size=page_size,
    )
    rows, total = await FinanceService.list_transactions(db, org_id, params)
    return {
        "items": [TransactionResponse.model_validate(r) for r in rows],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "/transactions",
    response_model=TransactionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_transaction(
    data: TransactionCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    """Create a finance transaction (auto-generates journal entry if accounts are configured)."""
    user_id = uuid.UUID(str(user["sub"]))
    return await FinanceService.create_transaction(db, org_id, user_id, data)


# ---------------------------------------------------------------------------
# Payment Accounts
# ---------------------------------------------------------------------------


@router.get(
    "/payment-accounts",
    response_model=list[PaymentAccountResponse],
)
async def list_payment_accounts(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List all payment account mappings."""
    return await FinanceService.list_payment_accounts(db, org_id)


@router.post(
    "/payment-accounts",
    response_model=PaymentAccountResponse,
    status_code=status.HTTP_201_CREATED,
)
async def set_payment_account(
    data: PaymentAccountCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Set (upsert) a payment-method-to-account mapping."""
    return await FinanceService.set_payment_account(db, org_id, data)
