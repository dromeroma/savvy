"""Business logic for the double-entry accounting engine."""

import calendar
import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.core.exceptions import NotFoundError, ValidationError
from src.modules.accounting.models import (
    ChartOfAccounts,
    FiscalPeriod,
    JournalEntry,
    JournalEntryLine,
)
from src.modules.accounting.schemas import (
    AccountCreate,
    AccountUpdate,
    JournalEntryLineCreate,
    JournalEntryLineResponse,
    JournalEntryResponse,
    ReportAccountLine,
)


class AccountingEngine:
    """Stateless service layer for accounting operations."""

    # ------------------------------------------------------------------
    # Chart of Accounts
    # ------------------------------------------------------------------

    @staticmethod
    async def list_accounts(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[ChartOfAccounts]:
        """List all accounts for an organization, ordered by code."""
        result = await db.execute(
            select(ChartOfAccounts)
            .where(ChartOfAccounts.organization_id == org_id)
            .order_by(ChartOfAccounts.code)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_account(
        db: AsyncSession, org_id: uuid.UUID, data: AccountCreate,
    ) -> ChartOfAccounts:
        """Create a new account in the chart of accounts."""
        account = ChartOfAccounts(
            organization_id=org_id,
            code=data.code,
            name=data.name,
            type=data.type,
            parent_id=data.parent_id,
            is_active=True,
            is_system=False,
        )
        db.add(account)
        await db.flush()
        await db.refresh(account)
        return account

    @staticmethod
    async def update_account(
        db: AsyncSession,
        org_id: uuid.UUID,
        account_id: uuid.UUID,
        data: AccountUpdate,
    ) -> ChartOfAccounts:
        """Update a non-system account."""
        result = await db.execute(
            select(ChartOfAccounts).where(
                ChartOfAccounts.id == account_id,
                ChartOfAccounts.organization_id == org_id,
            )
        )
        account = result.scalar_one_or_none()
        if account is None:
            raise NotFoundError("Account not found.")

        if account.is_system:
            raise ValidationError("System accounts cannot be modified.")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(account, field, value)

        await db.flush()
        await db.refresh(account)
        return account

    # ------------------------------------------------------------------
    # Fiscal Periods
    # ------------------------------------------------------------------

    @staticmethod
    async def get_or_create_period(
        db: AsyncSession, org_id: uuid.UUID, target_date: date,
        app_code: str | None = None,
    ) -> FiscalPeriod:
        """Find or create the fiscal period for the given date and app.

        Respects the org's fiscal_period_mode setting:
        - 'per_app' (default): separate periods per app_code
        - 'unified': one period for all apps (app_code ignored)
        """
        from src.modules.organization.models import Organization

        # Check org setting
        org_result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = org_result.scalar_one_or_none()
        mode = (org.settings or {}).get("fiscal_period_mode", "per_app") if org else "per_app"

        effective_app_code = app_code if mode == "per_app" else None

        year = target_date.year
        month = target_date.month

        stmt = select(FiscalPeriod).where(
            FiscalPeriod.organization_id == org_id,
            FiscalPeriod.year == year,
            FiscalPeriod.month == month,
        )
        if effective_app_code:
            stmt = stmt.where(FiscalPeriod.app_code == effective_app_code)
        else:
            stmt = stmt.where(FiscalPeriod.app_code.is_(None))

        result = await db.execute(stmt)
        period = result.scalar_one_or_none()
        if period is not None:
            return period

        last_day = calendar.monthrange(year, month)[1]
        period = FiscalPeriod(
            organization_id=org_id,
            year=year,
            month=month,
            app_code=effective_app_code,
            start_date=date(year, month, 1),
            end_date=date(year, month, last_day),
        )
        db.add(period)
        await db.flush()
        await db.refresh(period)
        return period

    @staticmethod
    async def list_periods(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[FiscalPeriod]:
        """List all fiscal periods for an organization."""
        result = await db.execute(
            select(FiscalPeriod)
            .where(FiscalPeriod.organization_id == org_id)
            .order_by(FiscalPeriod.year.desc(), FiscalPeriod.month.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def close_period(
        db: AsyncSession,
        org_id: uuid.UUID,
        period_id: uuid.UUID,
        closed_by: uuid.UUID,
    ) -> FiscalPeriod:
        """Close a fiscal period, preventing new entries."""
        result = await db.execute(
            select(FiscalPeriod).where(
                FiscalPeriod.id == period_id,
                FiscalPeriod.organization_id == org_id,
            )
        )
        period = result.scalar_one_or_none()
        if period is None:
            raise NotFoundError("Fiscal period not found.")

        if period.status == "closed":
            raise ValidationError("This fiscal period is already closed.")

        period.status = "closed"
        period.closed_by = closed_by
        period.closed_at = datetime.now(UTC)

        await db.flush()
        await db.refresh(period)
        return period

    # ------------------------------------------------------------------
    # Journal Entries
    # ------------------------------------------------------------------

    @staticmethod
    async def create_entry(
        db: AsyncSession,
        org_id: uuid.UUID,
        entry_date: date,
        description: str,
        created_by: uuid.UUID,
        lines: list[JournalEntryLineCreate],
        source_app: str | None = None,
        reference_type: str | None = None,
        reference_id: uuid.UUID | None = None,
    ) -> JournalEntry:
        """Create a balanced journal entry with lines.

        Validates that sum(debits) == sum(credits) before persisting.
        """
        if len(lines) < 2:
            raise ValidationError("A journal entry must have at least two lines.")

        # Validate balanced entry
        total_debit = sum(line.debit for line in lines)
        total_credit = sum(line.credit for line in lines)
        if total_debit != total_credit:
            raise ValidationError(
                f"Entry is not balanced. Total debits ({total_debit}) "
                f"must equal total credits ({total_credit})."
            )

        if total_debit == Decimal("0"):
            raise ValidationError("Entry must have non-zero amounts.")

        # Validate each line has either debit or credit but not both
        for line in lines:
            if line.debit < 0 or line.credit < 0:
                raise ValidationError("Debit and credit amounts must be non-negative.")
            if line.debit > 0 and line.credit > 0:
                raise ValidationError(
                    "A line cannot have both debit and credit amounts."
                )
            if line.debit == 0 and line.credit == 0:
                raise ValidationError(
                    "A line must have either a debit or credit amount."
                )

        # Find or create fiscal period
        period = await AccountingEngine.get_or_create_period(db, org_id, entry_date, source_app)
        if period.status == "closed":
            raise ValidationError("Cannot create entries in a closed fiscal period.")

        # Calculate next entry number for this org + period
        max_num_result = await db.execute(
            select(func.coalesce(func.max(JournalEntry.entry_number), 0)).where(
                JournalEntry.organization_id == org_id,
                JournalEntry.fiscal_period_id == period.id,
            )
        )
        next_number = max_num_result.scalar_one() + 1

        # Resolve account codes to IDs
        account_codes = [line.account_code for line in lines]
        accounts_result = await db.execute(
            select(ChartOfAccounts).where(
                ChartOfAccounts.organization_id == org_id,
                ChartOfAccounts.code.in_(account_codes),
                ChartOfAccounts.is_active == True,  # noqa: E712
            )
        )
        accounts_map = {acct.code: acct for acct in accounts_result.scalars().all()}

        # Validate all account codes exist
        missing_codes = set(account_codes) - set(accounts_map.keys())
        if missing_codes:
            raise ValidationError(
                f"Account codes not found or inactive: {', '.join(sorted(missing_codes))}"
            )

        # Create journal entry
        entry = JournalEntry(
            organization_id=org_id,
            fiscal_period_id=period.id,
            entry_number=next_number,
            date=entry_date,
            description=description,
            source_app=source_app,
            reference_type=reference_type,
            reference_id=reference_id,
            status="posted",
            created_by=created_by,
        )
        db.add(entry)
        await db.flush()

        # Create entry lines
        for line in lines:
            account = accounts_map[line.account_code]
            entry_line = JournalEntryLine(
                journal_entry_id=entry.id,
                account_id=account.id,
                debit=line.debit,
                credit=line.credit,
                description=line.description,
            )
            db.add(entry_line)

        await db.flush()

        # Reload with lines
        return await AccountingEngine.get_entry(db, org_id, entry.id)

    @staticmethod
    async def list_entries(
        db: AsyncSession,
        org_id: uuid.UUID,
        period_id: uuid.UUID | None = None,
        source_app: str | None = None,
    ) -> list[JournalEntry]:
        """List journal entries with optional filters."""
        stmt = (
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account))
            .where(JournalEntry.organization_id == org_id)
            .order_by(JournalEntry.date.desc(), JournalEntry.entry_number.desc())
        )

        if period_id is not None:
            stmt = stmt.where(JournalEntry.fiscal_period_id == period_id)
        if source_app is not None:
            stmt = stmt.where(JournalEntry.source_app == source_app)

        result = await db.execute(stmt)
        return list(result.scalars().unique().all())

    @staticmethod
    async def get_entry(
        db: AsyncSession, org_id: uuid.UUID, entry_id: uuid.UUID,
    ) -> JournalEntry:
        """Get a single journal entry with its lines."""
        result = await db.execute(
            select(JournalEntry)
            .options(selectinload(JournalEntry.lines).selectinload(JournalEntryLine.account))
            .where(
                JournalEntry.id == entry_id,
                JournalEntry.organization_id == org_id,
            )
        )
        entry = result.scalar_one_or_none()
        if entry is None:
            raise NotFoundError("Journal entry not found.")
        return entry

    # ------------------------------------------------------------------
    # Reports
    # ------------------------------------------------------------------

    @staticmethod
    async def income_statement(
        db: AsyncSession,
        org_id: uuid.UUID,
        start_date: date,
        end_date: date,
    ) -> dict:
        """Generate an income statement for the given date range.

        Revenue = sum(credit - debit) for revenue accounts.
        Expense = sum(debit - credit) for expense accounts.
        Net income = total_revenue - total_expense.
        """
        stmt = (
            select(
                ChartOfAccounts.code,
                ChartOfAccounts.name,
                ChartOfAccounts.type,
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
            )
            .join(JournalEntryLine, JournalEntryLine.account_id == ChartOfAccounts.id)
            .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
            .where(
                ChartOfAccounts.organization_id == org_id,
                ChartOfAccounts.type.in_(["revenue", "expense"]),
                JournalEntry.organization_id == org_id,
                JournalEntry.status == "posted",
                JournalEntry.date >= start_date,
                JournalEntry.date <= end_date,
            )
            .group_by(ChartOfAccounts.code, ChartOfAccounts.name, ChartOfAccounts.type)
            .order_by(ChartOfAccounts.code)
        )
        result = await db.execute(stmt)
        rows = result.all()

        revenues: list[ReportAccountLine] = []
        expenses: list[ReportAccountLine] = []

        for row in rows:
            if row.type == "revenue":
                amount = Decimal(str(row.total_credit)) - Decimal(str(row.total_debit))
                revenues.append(ReportAccountLine(code=row.code, name=row.name, amount=amount))
            elif row.type == "expense":
                amount = Decimal(str(row.total_debit)) - Decimal(str(row.total_credit))
                expenses.append(ReportAccountLine(code=row.code, name=row.name, amount=amount))

        total_revenue = sum(r.amount for r in revenues)
        total_expense = sum(e.amount for e in expenses)

        return {
            "revenues": revenues,
            "expenses": expenses,
            "total_revenue": total_revenue,
            "total_expense": total_expense,
            "net_income": total_revenue - total_expense,
        }

    @staticmethod
    async def balance_sheet(
        db: AsyncSession,
        org_id: uuid.UUID,
        as_of_date: date,
    ) -> dict:
        """Generate a balance sheet as of a specific date.

        Assets = sum(debit - credit).
        Liabilities = sum(credit - debit).
        Equity = sum(credit - debit) for equity accounts + net income to date.
        """
        stmt = (
            select(
                ChartOfAccounts.code,
                ChartOfAccounts.name,
                ChartOfAccounts.type,
                func.coalesce(func.sum(JournalEntryLine.debit), 0).label("total_debit"),
                func.coalesce(func.sum(JournalEntryLine.credit), 0).label("total_credit"),
            )
            .join(JournalEntryLine, JournalEntryLine.account_id == ChartOfAccounts.id)
            .join(JournalEntry, JournalEntry.id == JournalEntryLine.journal_entry_id)
            .where(
                ChartOfAccounts.organization_id == org_id,
                JournalEntry.organization_id == org_id,
                JournalEntry.status == "posted",
                JournalEntry.date <= as_of_date,
            )
            .group_by(ChartOfAccounts.code, ChartOfAccounts.name, ChartOfAccounts.type)
            .order_by(ChartOfAccounts.code)
        )
        result = await db.execute(stmt)
        rows = result.all()

        assets: list[ReportAccountLine] = []
        liabilities: list[ReportAccountLine] = []
        equity_accounts: list[ReportAccountLine] = []
        net_income = Decimal("0")

        for row in rows:
            total_debit = Decimal(str(row.total_debit))
            total_credit = Decimal(str(row.total_credit))

            if row.type == "asset":
                amount = total_debit - total_credit
                assets.append(ReportAccountLine(code=row.code, name=row.name, amount=amount))
            elif row.type == "liability":
                amount = total_credit - total_debit
                liabilities.append(ReportAccountLine(code=row.code, name=row.name, amount=amount))
            elif row.type == "equity":
                amount = total_credit - total_debit
                equity_accounts.append(ReportAccountLine(code=row.code, name=row.name, amount=amount))
            elif row.type == "revenue":
                net_income += total_credit - total_debit
            elif row.type == "expense":
                net_income -= total_debit - total_credit

        # Add retained earnings / net income as an equity line
        if net_income != Decimal("0"):
            equity_accounts.append(
                ReportAccountLine(
                    code="RE",
                    name="Resultado del Ejercicio",
                    amount=net_income,
                )
            )

        total_assets = sum(a.amount for a in assets)
        total_liabilities = sum(l.amount for l in liabilities)
        total_equity = sum(e.amount for e in equity_accounts)

        return {
            "assets": assets,
            "liabilities": liabilities,
            "equity": equity_accounts,
            "total_assets": total_assets,
            "total_liabilities": total_liabilities,
            "total_equity": total_equity,
        }
