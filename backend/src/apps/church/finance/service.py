"""Business logic for church income and expense management.

Delegates all persistence to the shared SavvyFinance engine via
FinanceService.  Church transactions are scoped by app_code="church".
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.finance.schemas import ExpenseCreate, IncomeCreate
from src.modules.finance.models import FinanceCategory, FinanceTransaction
from src.modules.finance.schemas import TransactionCreate, TransactionListParams
from src.modules.finance.service import FinanceService

APP_CODE = "church"


class ChurchFinanceService:
    """Thin wrapper that maps church-specific payloads to SavvyFinance."""

    # ------------------------------------------------------------------
    # Income
    # ------------------------------------------------------------------

    @staticmethod
    async def create_income(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: IncomeCreate,
    ) -> FinanceTransaction:
        """Create a church income via FinanceService."""
        txn_data = TransactionCreate(
            category_code=data.category_code,
            type="income",
            person_id=data.person_id,
            amount=data.amount,
            date=data.date,
            payment_method=data.payment_method,
            description=data.description,
            app_code=APP_CODE,
            reference_type="church_income",
        )
        return await FinanceService.create_transaction(db, org_id, user_id, txn_data)

    @staticmethod
    async def list_incomes(
        db: AsyncSession,
        org_id: uuid.UUID,
        period_id: uuid.UUID | None = None,
    ) -> tuple[list[FinanceTransaction], int]:
        """List church incomes, optionally filtered by fiscal period."""
        params = TransactionListParams(
            type="income",
            app_code=APP_CODE,
            page=1,
            page_size=100,
        )
        return await FinanceService.list_transactions(db, org_id, params)

    @staticmethod
    async def get_income(
        db: AsyncSession,
        org_id: uuid.UUID,
        income_id: uuid.UUID,
    ) -> FinanceTransaction:
        """Get a specific income by ID."""
        return await FinanceService.get_transaction(db, org_id, income_id)

    # ------------------------------------------------------------------
    # Expense
    # ------------------------------------------------------------------

    @staticmethod
    async def create_expense(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ExpenseCreate,
    ) -> FinanceTransaction:
        """Create a church expense via FinanceService."""
        txn_data = TransactionCreate(
            category_code=data.category_code,
            type="expense",
            amount=data.amount,
            date=data.date,
            payment_method=data.payment_method,
            description=data.description,
            vendor=data.vendor,
            app_code=APP_CODE,
            reference_type="church_expense",
        )
        return await FinanceService.create_transaction(db, org_id, user_id, txn_data)

    @staticmethod
    async def list_expenses(
        db: AsyncSession,
        org_id: uuid.UUID,
        period_id: uuid.UUID | None = None,
    ) -> tuple[list[FinanceTransaction], int]:
        """List church expenses, optionally filtered by fiscal period."""
        params = TransactionListParams(
            type="expense",
            app_code=APP_CODE,
            page=1,
            page_size=100,
        )
        return await FinanceService.list_transactions(db, org_id, params)

    @staticmethod
    async def get_expense(
        db: AsyncSession,
        org_id: uuid.UUID,
        expense_id: uuid.UUID,
    ) -> FinanceTransaction:
        """Get a specific expense by ID."""
        return await FinanceService.get_transaction(db, org_id, expense_id)

    # ------------------------------------------------------------------
    # Categories (read-only)
    # ------------------------------------------------------------------

    @staticmethod
    async def list_income_categories(
        db: AsyncSession,
        org_id: uuid.UUID,
    ) -> list[FinanceCategory]:
        """List church income categories."""
        return await FinanceService.list_categories(db, org_id, app_code=APP_CODE, type_="income")

    @staticmethod
    async def list_expense_categories(
        db: AsyncSession,
        org_id: uuid.UUID,
    ) -> list[FinanceCategory]:
        """List church expense categories."""
        return await FinanceService.list_categories(db, org_id, app_code=APP_CODE, type_="expense")
