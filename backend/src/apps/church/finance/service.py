"""Business logic for church income and expense management."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ForbiddenError, NotFoundError
from src.apps.church.finance.models import (
    ChurchExpense,
    ChurchExpenseCategory,
    ChurchIncome,
    ChurchIncomeCategory,
)
from src.apps.church.finance.schemas import (
    ExpenseCreate,
    ExpenseUpdate,
    IncomeCreate,
    IncomeUpdate,
)

# Mapping from payment_method to accounting account code
PAYMENT_ACCOUNT_MAP = {
    "cash": "1.1.01",      # Caja General
    "transfer": "1.1.02",  # Bancos
    "card": "1.1.02",      # Bancos
    "check": "1.1.02",     # Bancos
}


class ChurchFinanceService:
    """Handles income and expense operations, auto-generating journal entries."""

    # ------------------------------------------------------------------
    # Income
    # ------------------------------------------------------------------

    @staticmethod
    async def list_incomes(
        db: AsyncSession,
        org_id: uuid.UUID,
        period_id: uuid.UUID | None = None,
    ) -> list[ChurchIncome]:
        stmt = select(ChurchIncome).where(ChurchIncome.organization_id == org_id)
        if period_id:
            stmt = stmt.where(ChurchIncome.fiscal_period_id == period_id)
        stmt = stmt.order_by(ChurchIncome.date.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_income(
        db: AsyncSession, org_id: uuid.UUID, income_id: uuid.UUID,
    ) -> ChurchIncome:
        result = await db.execute(
            select(ChurchIncome).where(
                ChurchIncome.id == income_id,
                ChurchIncome.organization_id == org_id,
            )
        )
        income = result.scalar_one_or_none()
        if income is None:
            raise NotFoundError("Income not found.")
        return income

    @staticmethod
    async def create_income(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: IncomeCreate,
    ) -> ChurchIncome:
        """Create an income and auto-generate a journal entry."""
        # Resolve category
        cat_result = await db.execute(
            select(ChurchIncomeCategory).where(
                ChurchIncomeCategory.organization_id == org_id,
                ChurchIncomeCategory.code == data.category_code,
            )
        )
        category = cat_result.scalar_one_or_none()
        if category is None:
            raise NotFoundError(f"Income category '{data.category_code}' not found.")

        # Get or create fiscal period
        from src.modules.accounting.service import AccountingEngine

        period = await AccountingEngine.get_or_create_period(db, org_id, data.date)

        # Check period is open
        if period.status != "open":
            raise ForbiddenError("Cannot add income to a closed fiscal period.")

        # Create income record
        income = ChurchIncome(
            organization_id=org_id,
            category_id=category.id,
            church_member_id=data.church_member_id,
            amount=data.amount,
            date=data.date,
            payment_method=data.payment_method,
            description=data.description,
            fiscal_period_id=period.id,
            created_by=user_id,
        )
        db.add(income)
        await db.flush()

        # Auto-generate journal entry
        debit_account = PAYMENT_ACCOUNT_MAP.get(data.payment_method, "1.1.01")
        credit_account = category.account_id

        if credit_account is not None:
            # Resolve credit account code
            from src.modules.accounting.models import ChartOfAccounts
            acct = await db.execute(
                select(ChartOfAccounts).where(ChartOfAccounts.id == credit_account)
            )
            credit_account_obj = acct.scalar_one_or_none()
            credit_code = credit_account_obj.code if credit_account_obj else "4.1.04"
        else:
            credit_code = "4.1.04"  # Otros Ingresos fallback

        entry = await AccountingEngine.create_entry(
            db=db,
            org_id=org_id,
            entry_date=data.date,
            description=f"Ingreso: {category.name} - {data.description or ''}".strip(" -"),
            created_by=user_id,
            source_app="church",
            reference_type="church_income",
            reference_id=income.id,
            lines=[
                {"account_code": debit_account, "debit": data.amount, "credit": Decimal(0)},
                {"account_code": credit_code, "debit": Decimal(0), "credit": data.amount},
            ],
        )

        income.journal_entry_id = entry.id
        await db.flush()
        await db.refresh(income)
        return income

    # ------------------------------------------------------------------
    # Expense
    # ------------------------------------------------------------------

    @staticmethod
    async def list_expenses(
        db: AsyncSession,
        org_id: uuid.UUID,
        period_id: uuid.UUID | None = None,
    ) -> list[ChurchExpense]:
        stmt = select(ChurchExpense).where(ChurchExpense.organization_id == org_id)
        if period_id:
            stmt = stmt.where(ChurchExpense.fiscal_period_id == period_id)
        stmt = stmt.order_by(ChurchExpense.date.desc())
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_expense(
        db: AsyncSession, org_id: uuid.UUID, expense_id: uuid.UUID,
    ) -> ChurchExpense:
        result = await db.execute(
            select(ChurchExpense).where(
                ChurchExpense.id == expense_id,
                ChurchExpense.organization_id == org_id,
            )
        )
        expense = result.scalar_one_or_none()
        if expense is None:
            raise NotFoundError("Expense not found.")
        return expense

    @staticmethod
    async def create_expense(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: ExpenseCreate,
    ) -> ChurchExpense:
        """Create an expense and auto-generate a journal entry."""
        # Resolve category
        cat_result = await db.execute(
            select(ChurchExpenseCategory).where(
                ChurchExpenseCategory.organization_id == org_id,
                ChurchExpenseCategory.code == data.category_code,
            )
        )
        category = cat_result.scalar_one_or_none()
        if category is None:
            raise NotFoundError(f"Expense category '{data.category_code}' not found.")

        from src.modules.accounting.service import AccountingEngine

        period = await AccountingEngine.get_or_create_period(db, org_id, data.date)

        if period.status != "open":
            raise ForbiddenError("Cannot add expense to a closed fiscal period.")

        expense = ChurchExpense(
            organization_id=org_id,
            category_id=category.id,
            amount=data.amount,
            date=data.date,
            payment_method=data.payment_method,
            description=data.description,
            vendor=data.vendor,
            fiscal_period_id=period.id,
            created_by=user_id,
        )
        db.add(expense)
        await db.flush()

        # Auto-generate journal entry
        # Debit: expense account, Credit: payment source
        if category.account_id is not None:
            from src.modules.accounting.models import ChartOfAccounts
            acct = await db.execute(
                select(ChartOfAccounts).where(ChartOfAccounts.id == category.account_id)
            )
            debit_account_obj = acct.scalar_one_or_none()
            debit_code = debit_account_obj.code if debit_account_obj else "5.1.10"
        else:
            debit_code = "5.1.10"  # Otros Gastos fallback

        credit_account = PAYMENT_ACCOUNT_MAP.get(data.payment_method, "1.1.01")

        entry = await AccountingEngine.create_entry(
            db=db,
            org_id=org_id,
            entry_date=data.date,
            description=f"Gasto: {category.name} - {data.vendor or ''} {data.description or ''}".strip(" -"),
            created_by=user_id,
            source_app="church",
            reference_type="church_expense",
            reference_id=expense.id,
            lines=[
                {"account_code": debit_code, "debit": data.amount, "credit": Decimal(0)},
                {"account_code": credit_account, "debit": Decimal(0), "credit": data.amount},
            ],
        )

        expense.journal_entry_id = entry.id
        await db.flush()
        await db.refresh(expense)
        return expense

    # ------------------------------------------------------------------
    # Categories (read-only for now)
    # ------------------------------------------------------------------

    @staticmethod
    async def list_income_categories(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[ChurchIncomeCategory]:
        result = await db.execute(
            select(ChurchIncomeCategory)
            .where(ChurchIncomeCategory.organization_id == org_id)
            .order_by(ChurchIncomeCategory.code)
        )
        return list(result.scalars().all())

    @staticmethod
    async def list_expense_categories(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[ChurchExpenseCategory]:
        result = await db.execute(
            select(ChurchExpenseCategory)
            .where(ChurchExpenseCategory.organization_id == org_id)
            .order_by(ChurchExpenseCategory.code)
        )
        return list(result.scalars().all())
