"""Church report generation service.

Uses the shared SavvyFinance tables (finance_transactions + finance_categories)
instead of the legacy church-specific income/expense tables.
"""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.reports.schemas import (
    CategoryTotal,
    MonthlySummaryResponse,
    TitheOfTitheResponse,
)
from src.modules.accounting.models import FiscalPeriod
from src.modules.finance.models import FinanceCategory, FinanceTransaction

APP_CODE = "church"


class ChurchReportService:
    """Generates church-specific financial reports from SavvyFinance data."""

    @staticmethod
    async def monthly_summary(
        db: AsyncSession,
        org_id: uuid.UUID,
        year: int,
        month: int,
    ) -> MonthlySummaryResponse:
        """Generate a consolidated monthly report."""
        # Find the fiscal period
        period_result = await db.execute(
            select(FiscalPeriod).where(
                FiscalPeriod.organization_id == org_id,
                FiscalPeriod.year == year,
                FiscalPeriod.month == month,
            )
        )
        period = period_result.scalar_one_or_none()

        # No period = no transactions for this month → return zeros
        if period is None:
            tithe = TitheOfTitheResponse(
                total_tithes=Decimal(0), total_offerings=Decimal(0),
                base_amount=Decimal(0), tithe_of_tithe=Decimal(0),
            )
            return MonthlySummaryResponse(
                year=year, month=month,
                total_income=Decimal(0), total_expenses=Decimal(0), net=Decimal(0),
                income_by_category=[], expenses_by_category=[], tithe_of_tithe=tithe,
            )

        period_id = period.id

        # Income by category
        income_cats = await _transactions_by_category(db, org_id, period_id, "income")
        total_income = sum(c.total for c in income_cats)

        # Expenses by category
        expense_cats = await _transactions_by_category(db, org_id, period_id, "expense")
        total_expenses = sum(c.total for c in expense_cats)

        # Tithe of tithe
        tithe_of_tithe = await ChurchReportService.tithe_of_tithe(db, org_id, year, month)

        return MonthlySummaryResponse(
            year=year,
            month=month,
            total_income=total_income,
            total_expenses=total_expenses,
            net=total_income - total_expenses,
            income_by_category=income_cats,
            expenses_by_category=expense_cats,
            tithe_of_tithe=tithe_of_tithe,
        )

    @staticmethod
    async def tithe_of_tithe(
        db: AsyncSession,
        org_id: uuid.UUID,
        year: int,
        month: int,
    ) -> TitheOfTitheResponse:
        """Calculate the tithe of tithe: 10 % of (tithes + offerings)."""
        period_result = await db.execute(
            select(FiscalPeriod).where(
                FiscalPeriod.organization_id == org_id,
                FiscalPeriod.year == year,
                FiscalPeriod.month == month,
            )
        )
        period = period_result.scalar_one_or_none()

        if period is None:
            return TitheOfTitheResponse(
                total_tithes=Decimal(0), total_offerings=Decimal(0),
                base_amount=Decimal(0), tithe_of_tithe=Decimal(0),
            )

        period_id = period.id

        total_tithes = await _sum_by_category_code(db, org_id, period_id, "TITHE")
        total_offerings = await _sum_by_category_code(db, org_id, period_id, "OFFERING")

        base = total_tithes + total_offerings
        tithe_of_tithe = (base * Decimal("0.10")).quantize(Decimal("0.01"))

        return TitheOfTitheResponse(
            total_tithes=total_tithes,
            total_offerings=total_offerings,
            base_amount=base,
            tithe_of_tithe=tithe_of_tithe,
        )


# ---------------------------------------------------------------------------
# Helper queries
# ---------------------------------------------------------------------------


async def _transactions_by_category(
    db: AsyncSession,
    org_id: uuid.UUID,
    period_id: uuid.UUID | None,
    txn_type: str,
) -> list[CategoryTotal]:
    """Aggregate transaction amounts by category for a given type."""
    stmt = (
        select(
            FinanceCategory.name,
            FinanceCategory.code,
            func.coalesce(func.sum(FinanceTransaction.amount), 0).label("total"),
        )
        .join(
            FinanceTransaction,
            FinanceTransaction.category_id == FinanceCategory.id,
            isouter=True,
        )
        .where(
            FinanceCategory.organization_id == org_id,
            FinanceCategory.app_code == APP_CODE,
            FinanceCategory.type == txn_type,
        )
    )
    if period_id:
        stmt = stmt.where(FinanceTransaction.fiscal_period_id == period_id)

    stmt = stmt.group_by(FinanceCategory.name, FinanceCategory.code)
    stmt = stmt.order_by(FinanceCategory.code)

    result = await db.execute(stmt)
    return [
        CategoryTotal(category_name=row.name, category_code=row.code, total=row.total)
        for row in result.all()
    ]


async def _sum_by_category_code(
    db: AsyncSession,
    org_id: uuid.UUID,
    period_id: uuid.UUID | None,
    code: str,
) -> Decimal:
    """Sum transaction amounts for a specific category code within the church app."""
    stmt = (
        select(func.coalesce(func.sum(FinanceTransaction.amount), 0))
        .join(FinanceCategory, FinanceTransaction.category_id == FinanceCategory.id)
        .where(
            FinanceTransaction.organization_id == org_id,
            FinanceTransaction.app_code == APP_CODE,
            FinanceCategory.code == code,
        )
    )
    if period_id:
        stmt = stmt.where(FinanceTransaction.fiscal_period_id == period_id)

    result = await db.execute(stmt)
    return Decimal(str(result.scalar() or 0))
