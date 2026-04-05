"""Church report generation service."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.finance.models import (
    ChurchExpense,
    ChurchExpenseCategory,
    ChurchIncome,
    ChurchIncomeCategory,
)
from src.apps.church.reports.schemas import (
    CategoryTotal,
    MonthlySummaryResponse,
    TitheOfTitheResponse,
)
from src.modules.accounting.models import FiscalPeriod


class ChurchReportService:
    """Generates church-specific financial reports."""

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
        period_id = period.id if period else None

        # Income by category
        income_cats = await _income_by_category(db, org_id, period_id)
        total_income = sum(c.total for c in income_cats)

        # Expenses by category
        expense_cats = await _expenses_by_category(db, org_id, period_id)
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
        """Calculate the tithe of tithe: 10% of (tithes + offerings)."""
        period_result = await db.execute(
            select(FiscalPeriod).where(
                FiscalPeriod.organization_id == org_id,
                FiscalPeriod.year == year,
                FiscalPeriod.month == month,
            )
        )
        period = period_result.scalar_one_or_none()
        period_id = period.id if period else None

        total_tithes = await _sum_income_by_code(db, org_id, period_id, "TITHE")
        total_offerings = await _sum_income_by_code(db, org_id, period_id, "OFFERING")

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


async def _income_by_category(
    db: AsyncSession, org_id: uuid.UUID, period_id: uuid.UUID | None,
) -> list[CategoryTotal]:
    stmt = (
        select(
            ChurchIncomeCategory.name,
            ChurchIncomeCategory.code,
            func.coalesce(func.sum(ChurchIncome.amount), 0).label("total"),
        )
        .join(ChurchIncome, ChurchIncome.category_id == ChurchIncomeCategory.id, isouter=True)
        .where(ChurchIncomeCategory.organization_id == org_id)
    )
    if period_id:
        stmt = stmt.where(ChurchIncome.fiscal_period_id == period_id)
    stmt = stmt.group_by(ChurchIncomeCategory.name, ChurchIncomeCategory.code)
    stmt = stmt.order_by(ChurchIncomeCategory.code)

    result = await db.execute(stmt)
    return [
        CategoryTotal(category_name=row.name, category_code=row.code, total=row.total)
        for row in result.all()
    ]


async def _expenses_by_category(
    db: AsyncSession, org_id: uuid.UUID, period_id: uuid.UUID | None,
) -> list[CategoryTotal]:
    stmt = (
        select(
            ChurchExpenseCategory.name,
            ChurchExpenseCategory.code,
            func.coalesce(func.sum(ChurchExpense.amount), 0).label("total"),
        )
        .join(ChurchExpense, ChurchExpense.category_id == ChurchExpenseCategory.id, isouter=True)
        .where(ChurchExpenseCategory.organization_id == org_id)
    )
    if period_id:
        stmt = stmt.where(ChurchExpense.fiscal_period_id == period_id)
    stmt = stmt.group_by(ChurchExpenseCategory.name, ChurchExpenseCategory.code)
    stmt = stmt.order_by(ChurchExpenseCategory.code)

    result = await db.execute(stmt)
    return [
        CategoryTotal(category_name=row.name, category_code=row.code, total=row.total)
        for row in result.all()
    ]


async def _sum_income_by_code(
    db: AsyncSession, org_id: uuid.UUID, period_id: uuid.UUID | None, code: str,
) -> Decimal:
    stmt = (
        select(func.coalesce(func.sum(ChurchIncome.amount), 0))
        .join(ChurchIncomeCategory, ChurchIncome.category_id == ChurchIncomeCategory.id)
        .where(
            ChurchIncome.organization_id == org_id,
            ChurchIncomeCategory.code == code,
        )
    )
    if period_id:
        stmt = stmt.where(ChurchIncome.fiscal_period_id == period_id)

    result = await db.execute(stmt)
    return Decimal(str(result.scalar() or 0))
