"""FastAPI router for the Accounting module."""

import uuid
from datetime import date
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.modules.accounting.schemas import (
    AccountCreate,
    AccountResponse,
    AccountUpdate,
    BalanceSheetResponse,
    FiscalPeriodCreate,
    FiscalPeriodResponse,
    IncomeStatementResponse,
    JournalEntryCreate,
    JournalEntryLineResponse,
    JournalEntryResponse,
)
from src.modules.accounting.service import AccountingEngine

router = APIRouter(prefix="/accounting", tags=["Accounting"])

_READ = [Depends(require_permission("accounting", "reports.view", "entries.create", "chart.manage"))]
_CHART_WRITE = [Depends(require_permission("accounting", "chart.manage"))]
_PERIOD_CLOSE = [Depends(require_permission("accounting", "periods.close"))]
_ENTRY_CREATE = [Depends(require_permission("accounting", "entries.create"))]
_REPORTS = [Depends(require_permission("accounting", "reports.view"))]


# ---------------------------------------------------------------------------
# Chart of Accounts
# ---------------------------------------------------------------------------


@router.get(
    "/chart-of-accounts",
    response_model=list[AccountResponse],
    dependencies=_READ,
)
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List all accounts in the chart of accounts."""
    return await AccountingEngine.list_accounts(db, org_id)


@router.post(
    "/chart-of-accounts",
    response_model=AccountResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_CHART_WRITE,
)
async def create_account(
    data: AccountCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Create a new account in the chart of accounts."""
    return await AccountingEngine.create_account(db, org_id, data)


@router.patch(
    "/chart-of-accounts/{account_id}",
    response_model=AccountResponse,
    dependencies=_CHART_WRITE,
)
async def update_account(
    account_id: uuid.UUID,
    data: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Update an existing account (non-system accounts only)."""
    return await AccountingEngine.update_account(db, org_id, account_id, data)


# ---------------------------------------------------------------------------
# Fiscal Periods
# ---------------------------------------------------------------------------


@router.get(
    "/fiscal-periods",
    response_model=list[FiscalPeriodResponse],
    dependencies=_READ,
)
async def list_periods(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List all fiscal periods for the organization."""
    return await AccountingEngine.list_periods(db, org_id)


@router.post(
    "/fiscal-periods",
    response_model=FiscalPeriodResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_PERIOD_CLOSE,
)
async def create_period(
    data: FiscalPeriodCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Create a new fiscal period."""
    from datetime import date as date_type

    target_date = date_type(data.year, data.month, 1)
    return await AccountingEngine.get_or_create_period(db, org_id, target_date)


@router.post(
    "/fiscal-periods/{period_id}/close",
    response_model=FiscalPeriodResponse,
    dependencies=_PERIOD_CLOSE,
)
async def close_period(
    period_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    """Close a fiscal period, preventing new journal entries."""
    closed_by = uuid.UUID(str(user["sub"]))
    return await AccountingEngine.close_period(db, org_id, period_id, closed_by)


# ---------------------------------------------------------------------------
# Journal Entries
# ---------------------------------------------------------------------------


def _entry_to_response(entry: Any) -> JournalEntryResponse:
    """Convert a JournalEntry ORM object to its response schema."""
    return JournalEntryResponse(
        id=entry.id,
        entry_number=entry.entry_number,
        date=entry.date,
        description=entry.description,
        source_app=entry.source_app,
        reference_type=entry.reference_type,
        status=entry.status,
        created_at=entry.created_at,
        lines=[
            JournalEntryLineResponse(
                id=line.id,
                account_id=line.account_id,
                account_code=line.account.code,
                account_name=line.account.name,
                debit=line.debit,
                credit=line.credit,
                description=line.description,
            )
            for line in entry.lines
        ],
    )


@router.get(
    "/journal-entries",
    response_model=list[JournalEntryResponse],
    dependencies=_READ,
)
async def list_entries(
    period_id: uuid.UUID | None = Query(default=None),
    source_app: str | None = Query(default=None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List journal entries with optional filters."""
    entries = await AccountingEngine.list_entries(db, org_id, period_id, source_app)
    return [_entry_to_response(e) for e in entries]


@router.get(
    "/journal-entries/{entry_id}",
    response_model=JournalEntryResponse,
    dependencies=_READ,
)
async def get_entry(
    entry_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Get a single journal entry with its lines."""
    entry = await AccountingEngine.get_entry(db, org_id, entry_id)
    return _entry_to_response(entry)


@router.post(
    "/journal-entries",
    response_model=JournalEntryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_ENTRY_CREATE,
)
async def create_entry(
    data: JournalEntryCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    """Create a manual journal entry (must be balanced)."""
    created_by = uuid.UUID(str(user["sub"]))
    entry = await AccountingEngine.create_entry(
        db=db,
        org_id=org_id,
        entry_date=data.date,
        description=data.description,
        created_by=created_by,
        lines=data.lines,
    )
    return _entry_to_response(entry)


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


@router.get(
    "/reports/income-statement",
    response_model=IncomeStatementResponse,
    dependencies=_REPORTS,
)
async def income_statement(
    start_date: date = Query(...),
    end_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Generate an income statement for the given date range."""
    return await AccountingEngine.income_statement(db, org_id, start_date, end_date)


@router.get(
    "/reports/balance-sheet",
    response_model=BalanceSheetResponse,
    dependencies=_REPORTS,
)
async def balance_sheet(
    as_of_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Generate a balance sheet as of a specific date."""
    return await AccountingEngine.balance_sheet(db, org_id, as_of_date)
