"""SavvyCredit dashboard KPIs."""

from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.credit.loans.models import CreditLoan
from src.apps.credit.borrowers.models import CreditBorrower


class CreditDashboardService:

    @staticmethod
    async def get_kpis(db: AsyncSession, org_id: uuid.UUID) -> dict:
        # Active loans count and total portfolio
        loans_result = await db.execute(
            select(
                func.count().label("active_loans"),
                func.coalesce(func.sum(CreditLoan.balance_principal), 0).label("total_portfolio"),
                func.coalesce(func.sum(CreditLoan.balance_interest), 0).label("total_interest_receivable"),
                func.coalesce(func.sum(CreditLoan.balance_penalties), 0).label("total_penalties"),
            ).where(
                CreditLoan.organization_id == org_id,
                CreditLoan.status.in_(["active", "current", "delinquent"]),
            )
        )
        row = loans_result.one()

        # Delinquent loans
        delinquent_result = await db.execute(
            select(
                func.count().label("delinquent_count"),
                func.coalesce(func.sum(CreditLoan.balance_principal), 0).label("delinquent_amount"),
            ).where(
                CreditLoan.organization_id == org_id,
                CreditLoan.status == "delinquent",
            )
        )
        delinquent = delinquent_result.one()

        # Borrowers count
        borrowers_result = await db.execute(
            select(func.count()).where(
                CreditBorrower.organization_id == org_id,
                CreditBorrower.status == "active",
            )
        )
        total_borrowers = borrowers_result.scalar() or 0

        # Total disbursed (all time)
        disbursed_result = await db.execute(
            select(func.coalesce(func.sum(CreditLoan.principal), 0)).where(
                CreditLoan.organization_id == org_id,
            )
        )
        total_disbursed = float(disbursed_result.scalar() or 0)

        # Total collected
        collected_result = await db.execute(
            select(func.coalesce(func.sum(CreditLoan.total_paid), 0)).where(
                CreditLoan.organization_id == org_id,
            )
        )
        total_collected = float(collected_result.scalar() or 0)

        portfolio = float(row.total_portfolio)
        delinquent_amt = float(delinquent.delinquent_amount)

        return {
            "active_loans": row.active_loans,
            "total_portfolio": portfolio,
            "total_interest_receivable": float(row.total_interest_receivable),
            "total_penalties": float(row.total_penalties),
            "delinquent_loans": delinquent.delinquent_count,
            "delinquent_amount": delinquent_amt,
            "delinquency_rate": round((delinquent_amt / portfolio * 100) if portfolio > 0 else 0, 2),
            "total_borrowers": total_borrowers,
            "total_disbursed": total_disbursed,
            "total_collected": total_collected,
        }
