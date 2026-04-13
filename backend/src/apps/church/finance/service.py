"""Business logic for church income and expense management.

Delegates all persistence to the shared SavvyFinance engine via
FinanceService.  Church transactions are scoped by app_code="church".
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from decimal import Decimal

from sqlalchemy import select

from src.apps.church.finance.aggregate_models import ChurchAggregateOffering
from src.apps.church.finance.schemas import (
    AggregateOfferingCreate,
    ExpenseCreate,
    IncomeCreate,
)
from src.core.exceptions import NotFoundError, ValidationError
from src.modules.accounting.models import ChartOfAccounts
from src.modules.accounting.schemas import JournalEntryLineCreate
from src.modules.accounting.service import AccountingEngine
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

    # ------------------------------------------------------------------
    # Person Financial History
    # ------------------------------------------------------------------

    @staticmethod
    async def get_person_history(
        db: AsyncSession,
        org_id: uuid.UUID,
        person_id: uuid.UUID,
    ) -> dict:
        """Get all church transactions for a specific person."""
        from sqlalchemy import func

        stmt = (
            select(FinanceTransaction)
            .where(
                FinanceTransaction.organization_id == org_id,
                FinanceTransaction.app_code == APP_CODE,
                FinanceTransaction.person_id == person_id,
            )
            .order_by(FinanceTransaction.date.desc())
        )
        result = await db.execute(stmt)
        transactions = list(result.scalars().all())

        # Totals
        total_income = sum(
            t.amount for t in transactions if t.type == "income"
        )
        total_expenses = sum(
            t.amount for t in transactions if t.type == "expense"
        )

        # Map category names
        cat_ids = {t.category_id for t in transactions}
        cat_map: dict[uuid.UUID, str] = {}
        if cat_ids:
            cat_result = await db.execute(
                select(FinanceCategory.id, FinanceCategory.name).where(
                    FinanceCategory.id.in_(cat_ids)
                )
            )
            cat_map = {row.id: row.name for row in cat_result.all()}

        items = [
            {
                "id": str(t.id),
                "type": t.type,
                "amount": float(t.amount),
                "date": str(t.date),
                "category": cat_map.get(t.category_id, ""),
                "description": t.description,
                "payment_method": t.payment_method,
            }
            for t in transactions
        ]

        return {
            "person_id": str(person_id),
            "total_income": float(total_income),
            "total_expenses": float(total_expenses),
            "net": float(total_income - total_expenses),
            "count": len(items),
            "transactions": items,
        }

    # ------------------------------------------------------------------
    # Void Transaction
    # ------------------------------------------------------------------

    @staticmethod
    async def void_transaction(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        transaction_id: uuid.UUID,
    ) -> FinanceTransaction:
        """Void a transaction by setting amount to 0 and creating reversal entry."""
        txn = await FinanceService.get_transaction(db, org_id, transaction_id)

        if txn.app_code != APP_CODE:
            raise ValidationError("Transaction does not belong to the church app.")

        if txn.amount == 0:
            raise ValidationError("Transaction is already voided.")

        original_amount = txn.amount
        txn.amount = Decimal("0")
        txn.description = f"[ANULADA] {txn.description or ''}"

        # If there was a journal entry, create a reversal
        if txn.journal_entry_id:
            from src.modules.accounting.models import JournalEntry, JournalEntryLine

            je_result = await db.execute(
                select(JournalEntry).where(JournalEntry.id == txn.journal_entry_id)
            )
            original_je = je_result.scalar_one_or_none()

            if original_je:
                lines_result = await db.execute(
                    select(JournalEntryLine).where(
                        JournalEntryLine.journal_entry_id == original_je.id
                    )
                )
                original_lines = list(lines_result.scalars().all())

                # Resolve account codes
                acct_ids = [line.account_id for line in original_lines]
                acct_result = await db.execute(
                    select(ChartOfAccounts).where(
                        ChartOfAccounts.id.in_(acct_ids),
                        ChartOfAccounts.organization_id == org_id,
                    )
                )
                acct_map = {a.id: a.code for a in acct_result.scalars().all()}

                # Reverse: swap debit/credit
                reversal_lines = [
                    JournalEntryLineCreate(
                        account_code=acct_map[line.account_id],
                        debit=Decimal(str(line.credit)),
                        credit=Decimal(str(line.debit)),
                    )
                    for line in original_lines
                    if line.account_id in acct_map
                ]

                if reversal_lines:
                    await AccountingEngine.create_entry(
                        db=db,
                        org_id=org_id,
                        entry_date=txn.date,
                        description=f"Anulación: {original_je.description}",
                        created_by=user_id,
                        lines=reversal_lines,
                        source_app=APP_CODE,
                        reference_type="void_finance_transaction",
                        reference_id=txn.id,
                    )

        await db.flush()
        await db.refresh(txn)
        return txn

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

    # ------------------------------------------------------------------
    # Aggregate Offerings
    # ------------------------------------------------------------------

    @staticmethod
    async def list_aggregate_offerings(
        db: AsyncSession,
        org_id: uuid.UUID,
        event_id: uuid.UUID | None = None,
    ) -> list[ChurchAggregateOffering]:
        """List aggregate offerings, optionally filtered by event."""
        stmt = (
            select(ChurchAggregateOffering)
            .where(ChurchAggregateOffering.organization_id == org_id)
            .order_by(ChurchAggregateOffering.collected_date.desc())
        )
        if event_id:
            stmt = stmt.where(ChurchAggregateOffering.event_id == event_id)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_aggregate_offering(
        db: AsyncSession,
        org_id: uuid.UUID,
        user_id: uuid.UUID,
        data: AggregateOfferingCreate,
    ) -> ChurchAggregateOffering:
        """Create an aggregate offering and mirror it in finance_transactions."""
        # 1. Create the aggregate record (without FK yet).
        offering = ChurchAggregateOffering(
            organization_id=org_id,
            event_id=data.event_id,
            scope_id=data.scope_id,
            offering_type=data.offering_type,
            total_amount=data.total_amount,
            contributor_count=data.contributor_count,
            payment_method=data.payment_method,
            collected_date=data.collected_date,
            notes=data.notes,
            created_by=None,  # tracked via finance txn created_by instead
        )
        db.add(offering)
        await db.flush()
        await db.refresh(offering)

        # 2. Mirror into the shared finance_transactions ledger.
        txn_data = TransactionCreate(
            category_code=data.category_code,
            type="income",
            amount=data.total_amount,
            date=data.collected_date,
            payment_method=data.payment_method,
            description=(
                data.notes
                or f"Ofrenda agregada ({data.offering_type}) — "
                f"{data.contributor_count or 0} contribuyentes"
            ),
            app_code=APP_CODE,
            reference_type="church_aggregate_offering",
            reference_id=offering.id,
            scope_id=data.scope_id,
        )
        txn = await FinanceService.create_transaction(db, org_id, user_id, txn_data)

        # 3. Link the ledger row back to the aggregate.
        offering.finance_transaction_id = txn.id
        await db.flush()
        await db.refresh(offering)
        return offering
