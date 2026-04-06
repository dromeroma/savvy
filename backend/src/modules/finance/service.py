"""Business logic for the SavvyFinance income/expense engine."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.accounting.models import ChartOfAccounts
from src.modules.accounting.schemas import JournalEntryLineCreate
from src.modules.accounting.service import AccountingEngine
from src.modules.finance.models import (
    FinanceCategory,
    FinancePaymentAccount,
    FinanceTransaction,
)
from src.modules.finance.schemas import (
    CategoryCreate,
    CategorySummaryLine,
    PaymentAccountCreate,
    TransactionCreate,
    TransactionListParams,
    TransactionSummary,
)


class FinanceService:
    """Stateless service layer for finance operations."""

    # ------------------------------------------------------------------
    # Categories
    # ------------------------------------------------------------------

    @staticmethod
    async def list_categories(
        db: AsyncSession,
        org_id: uuid.UUID,
        app_code: str | None = None,
        type_: str | None = None,
    ) -> list[FinanceCategory]:
        """List finance categories with optional filters."""
        stmt = (
            select(FinanceCategory)
            .where(FinanceCategory.organization_id == org_id)
            .order_by(FinanceCategory.type, FinanceCategory.code)
        )
        if app_code is not None:
            stmt = stmt.where(FinanceCategory.app_code == app_code)
        if type_ is not None:
            stmt = stmt.where(FinanceCategory.type == type_)

        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_category(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: CategoryCreate,
    ) -> FinanceCategory:
        """Create a new finance category."""
        category = FinanceCategory(
            organization_id=org_id,
            app_code=data.app_code,
            type=data.type,
            name=data.name,
            code=data.code,
            account_id=data.account_id,
            is_system=False,
        )
        db.add(category)
        await db.flush()
        await db.refresh(category)
        return category

    @staticmethod
    async def get_category_by_code(
        db: AsyncSession,
        org_id: uuid.UUID,
        app_code: str | None,
        code: str,
    ) -> FinanceCategory:
        """Resolve a category by its unique (org, app_code, code) tuple."""
        stmt = select(FinanceCategory).where(
            FinanceCategory.organization_id == org_id,
            FinanceCategory.code == code,
        )
        if app_code is not None:
            stmt = stmt.where(FinanceCategory.app_code == app_code)
        else:
            stmt = stmt.where(FinanceCategory.app_code.is_(None))

        result = await db.execute(stmt)
        category = result.scalar_one_or_none()
        if category is None:
            raise NotFoundError(
                f"Finance category '{code}' not found for app_code '{app_code}'."
            )
        return category

    # ------------------------------------------------------------------
    # Transactions
    # ------------------------------------------------------------------

    @staticmethod
    async def list_transactions(
        db: AsyncSession,
        org_id: uuid.UUID,
        params: TransactionListParams,
    ) -> tuple[list[FinanceTransaction], int]:
        """List transactions with filters and pagination. Returns (rows, total)."""
        base = select(FinanceTransaction).where(
            FinanceTransaction.organization_id == org_id,
        )

        if params.type is not None:
            base = base.where(FinanceTransaction.type == params.type)
        if params.app_code is not None:
            base = base.where(FinanceTransaction.app_code == params.app_code)
        if params.date_from is not None:
            base = base.where(FinanceTransaction.date >= params.date_from)
        if params.date_to is not None:
            base = base.where(FinanceTransaction.date <= params.date_to)
        if params.category_code is not None:
            base = base.where(
                FinanceTransaction.category_id.in_(
                    select(FinanceCategory.id).where(
                        FinanceCategory.organization_id == org_id,
                        FinanceCategory.code == params.category_code,
                    )
                )
            )

        # Total count
        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await db.execute(count_stmt)).scalar_one()

        # Paginated rows
        offset = (params.page - 1) * params.page_size
        rows_stmt = (
            base
            .order_by(FinanceTransaction.date.desc(), FinanceTransaction.created_at.desc())
            .offset(offset)
            .limit(params.page_size)
        )
        result = await db.execute(rows_stmt)
        return list(result.scalars().all()), total

    @staticmethod
    async def create_transaction(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: TransactionCreate,
    ) -> FinanceTransaction:
        """Create a finance transaction with optional automatic journal entry.

        Flow:
        1. Resolve category by code
        2. Get or create fiscal period
        3. Validate period is open
        4. Save transaction
        5. Resolve debit/credit accounts from payment accounts mapping
        6. If both accounts resolved, create journal entry
        7. Link journal entry to transaction
        """
        # 1. Resolve category
        category = await FinanceService.get_category_by_code(
            db, org_id, data.app_code, data.category_code,
        )

        # 2. Get or create fiscal period
        period = await AccountingEngine.get_or_create_period(db, org_id, data.date)

        # 3. Check period is open
        if period.status == "closed":
            raise ValidationError("Cannot create transactions in a closed fiscal period.")

        # 4. Save transaction
        txn = FinanceTransaction(
            organization_id=org_id,
            category_id=category.id,
            type=data.type,
            person_id=data.person_id,
            amount=data.amount,
            date=data.date,
            payment_method=data.payment_method,
            description=data.description,
            vendor=data.vendor,
            app_code=data.app_code,
            reference_type=data.reference_type,
            reference_id=data.reference_id,
            scope_id=data.scope_id,
            fiscal_period_id=period.id,
            created_by=user_id,
        )
        db.add(txn)
        await db.flush()

        # 5. Resolve payment account (debit/credit counterpart)
        payment_account_id = await FinanceService.get_payment_account(
            db, org_id, data.payment_method,
        )
        category_account_id = category.account_id

        # 6. If both accounts resolved, create journal entry
        if payment_account_id is not None and category_account_id is not None:
            # Resolve account codes for journal entry lines
            acct_result = await db.execute(
                select(ChartOfAccounts).where(
                    ChartOfAccounts.id.in_([payment_account_id, category_account_id]),
                    ChartOfAccounts.organization_id == org_id,
                )
            )
            accounts_map = {acct.id: acct.code for acct in acct_result.scalars().all()}

            payment_code = accounts_map.get(payment_account_id)
            category_code = accounts_map.get(category_account_id)

            if payment_code and category_code:
                if data.type == "income":
                    debit_code = payment_code
                    credit_code = category_code
                else:  # expense
                    debit_code = category_code
                    credit_code = payment_code

                description = (
                    f"{data.type.capitalize()}: {category.name}"
                    + (f" - {data.description}" if data.description else "")
                )

                lines = [
                    JournalEntryLineCreate(
                        account_code=debit_code,
                        debit=data.amount,
                        credit=Decimal("0"),
                    ),
                    JournalEntryLineCreate(
                        account_code=credit_code,
                        debit=Decimal("0"),
                        credit=data.amount,
                    ),
                ]

                entry = await AccountingEngine.create_entry(
                    db=db,
                    org_id=org_id,
                    entry_date=data.date,
                    description=description,
                    created_by=user_id,
                    lines=lines,
                    source_app=data.app_code or "finance",
                    reference_type=data.reference_type or "finance_transaction",
                    reference_id=txn.id,
                )

                # 7. Link journal entry to transaction
                txn.journal_entry_id = entry.id
                await db.flush()

        await db.refresh(txn)
        return txn

    @staticmethod
    async def get_transaction(
        db: AsyncSession,
        org_id: uuid.UUID,
        transaction_id: uuid.UUID,
    ) -> FinanceTransaction:
        """Get a single transaction by ID."""
        result = await db.execute(
            select(FinanceTransaction).where(
                FinanceTransaction.id == transaction_id,
                FinanceTransaction.organization_id == org_id,
            )
        )
        txn = result.scalar_one_or_none()
        if txn is None:
            raise NotFoundError("Transaction not found.")
        return txn

    @staticmethod
    async def get_summary(
        db: AsyncSession,
        org_id: uuid.UUID,
        date_from: date,
        date_to: date,
        app_code: str | None = None,
    ) -> TransactionSummary:
        """Aggregate income/expense summary for a date range."""
        base = select(
            FinanceCategory.code,
            FinanceCategory.name,
            FinanceTransaction.type,
            func.coalesce(func.sum(FinanceTransaction.amount), 0).label("total"),
        ).join(
            FinanceCategory, FinanceCategory.id == FinanceTransaction.category_id,
        ).where(
            FinanceTransaction.organization_id == org_id,
            FinanceTransaction.date >= date_from,
            FinanceTransaction.date <= date_to,
        ).group_by(
            FinanceCategory.code,
            FinanceCategory.name,
            FinanceTransaction.type,
        ).order_by(
            FinanceTransaction.type,
            FinanceCategory.code,
        )

        if app_code is not None:
            base = base.where(FinanceTransaction.app_code == app_code)

        result = await db.execute(base)
        rows = result.all()

        total_income = Decimal("0")
        total_expenses = Decimal("0")
        by_category: list[CategorySummaryLine] = []

        for row in rows:
            amount = Decimal(str(row.total))
            by_category.append(
                CategorySummaryLine(code=row.code, name=row.name, total=amount),
            )
            if row.type == "income":
                total_income += amount
            else:
                total_expenses += amount

        return TransactionSummary(
            total_income=total_income,
            total_expenses=total_expenses,
            net=total_income - total_expenses,
            by_category=by_category,
        )

    # ------------------------------------------------------------------
    # Payment Accounts
    # ------------------------------------------------------------------

    @staticmethod
    async def list_payment_accounts(
        db: AsyncSession,
        org_id: uuid.UUID,
    ) -> list[FinancePaymentAccount]:
        """List all payment account mappings for an organization."""
        result = await db.execute(
            select(FinancePaymentAccount)
            .where(FinancePaymentAccount.organization_id == org_id)
            .order_by(FinancePaymentAccount.payment_method)
        )
        return list(result.scalars().all())

    @staticmethod
    async def set_payment_account(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: PaymentAccountCreate,
    ) -> FinancePaymentAccount:
        """Upsert a payment-method-to-account mapping."""
        result = await db.execute(
            select(FinancePaymentAccount).where(
                FinancePaymentAccount.organization_id == org_id,
                FinancePaymentAccount.payment_method == data.payment_method,
            )
        )
        existing = result.scalar_one_or_none()

        if existing is not None:
            existing.account_id = data.account_id
            await db.flush()
            await db.refresh(existing)
            return existing

        mapping = FinancePaymentAccount(
            organization_id=org_id,
            payment_method=data.payment_method,
            account_id=data.account_id,
        )
        db.add(mapping)
        await db.flush()
        await db.refresh(mapping)
        return mapping

    @staticmethod
    async def get_payment_account(
        db: AsyncSession,
        org_id: uuid.UUID,
        payment_method: str,
    ) -> uuid.UUID | None:
        """Resolve the chart-of-accounts ID for a given payment method, or None."""
        result = await db.execute(
            select(FinancePaymentAccount.account_id).where(
                FinancePaymentAccount.organization_id == org_id,
                FinancePaymentAccount.payment_method == payment_method,
            )
        )
        return result.scalar_one_or_none()
