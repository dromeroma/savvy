"""Church finance REST endpoints: income, expenses, categories."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, get_org_id
from src.apps.church.finance.schemas import (
    ExpenseCategoryResponse,
    ExpenseCreate,
    ExpenseResponse,
    IncomeCategoryResponse,
    IncomeCreate,
    IncomeResponse,
)
from src.apps.church.finance.service import ChurchFinanceService

router = APIRouter(prefix="/finance", tags=["Church Finance"])


# ---------------------------------------------------------------------------
# Income
# ---------------------------------------------------------------------------


@router.get("/income", response_model=list[IncomeResponse])
async def list_incomes(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    period_id: uuid.UUID | None = Query(None),
) -> Any:
    """List church incomes, optionally filtered by fiscal period."""
    return await ChurchFinanceService.list_incomes(db, org_id, period_id)


@router.post(
    "/income",
    response_model=IncomeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_income(
    data: IncomeCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Register a new income (tithe, offering, donation, etc.)."""
    return await ChurchFinanceService.create_income(
        db, org_id, uuid.UUID(current_user["sub"]), data,
    )


@router.get("/income/{income_id}", response_model=IncomeResponse)
async def get_income(
    income_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Get a specific income by ID."""
    return await ChurchFinanceService.get_income(db, org_id, income_id)


# ---------------------------------------------------------------------------
# Expenses
# ---------------------------------------------------------------------------


@router.get("/expenses", response_model=list[ExpenseResponse])
async def list_expenses(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    period_id: uuid.UUID | None = Query(None),
) -> Any:
    """List church expenses, optionally filtered by fiscal period."""
    return await ChurchFinanceService.list_expenses(db, org_id, period_id)


@router.post(
    "/expenses",
    response_model=ExpenseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_expense(
    data: ExpenseCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    current_user: dict = Depends(get_current_user),
) -> Any:
    """Register a new expense."""
    return await ChurchFinanceService.create_expense(
        db, org_id, uuid.UUID(current_user["sub"]), data,
    )


@router.get("/expenses/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Get a specific expense by ID."""
    return await ChurchFinanceService.get_expense(db, org_id, expense_id)


# ---------------------------------------------------------------------------
# Categories
# ---------------------------------------------------------------------------


@router.get("/categories/income", response_model=list[IncomeCategoryResponse])
async def list_income_categories(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List income categories for this church."""
    return await ChurchFinanceService.list_income_categories(db, org_id)


@router.get("/categories/expenses", response_model=list[ExpenseCategoryResponse])
async def list_expense_categories(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List expense categories for this church."""
    return await ChurchFinanceService.list_expense_categories(db, org_id)
