"""Church dashboard KPIs service."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.congregants.models import ChurchCongregant
from src.modules.finance.models import FinanceTransaction
from src.modules.people.models import Person

APP_CODE = "church"


class ChurchDashboardService:
    """Aggregates KPI data for the church dashboard."""

    @staticmethod
    async def get_kpis(
        db: AsyncSession,
        org_id: uuid.UUID,
    ) -> dict:
        today = date.today()
        first_of_month = today.replace(day=1)

        # Total active congregants
        active_count = (
            await db.execute(
                select(func.count(ChurchCongregant.id))
                .join(Person, Person.id == ChurchCongregant.person_id)
                .where(
                    ChurchCongregant.organization_id == org_id,
                    Person.status == "active",
                )
            )
        ).scalar_one()

        # Inactive congregants
        inactive_count = (
            await db.execute(
                select(func.count(ChurchCongregant.id))
                .join(Person, Person.id == ChurchCongregant.person_id)
                .where(
                    ChurchCongregant.organization_id == org_id,
                    Person.status == "inactive",
                )
            )
        ).scalar_one()

        # New congregants this month
        new_this_month = (
            await db.execute(
                select(func.count(ChurchCongregant.id)).where(
                    ChurchCongregant.organization_id == org_id,
                    func.date(ChurchCongregant.created_at) >= first_of_month,
                )
            )
        ).scalar_one()

        # Income this month
        income_month = (
            await db.execute(
                select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
                    FinanceTransaction.organization_id == org_id,
                    FinanceTransaction.app_code == APP_CODE,
                    FinanceTransaction.type == "income",
                    FinanceTransaction.date >= first_of_month,
                    FinanceTransaction.date <= today,
                )
            )
        ).scalar_one()

        # Expenses this month
        expenses_month = (
            await db.execute(
                select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
                    FinanceTransaction.organization_id == org_id,
                    FinanceTransaction.app_code == APP_CODE,
                    FinanceTransaction.type == "expense",
                    FinanceTransaction.date >= first_of_month,
                    FinanceTransaction.date <= today,
                )
            )
        ).scalar_one()

        # Income last month for comparison
        if today.month == 1:
            lm_start = date(today.year - 1, 12, 1)
            lm_end = date(today.year - 1, 12, 31)
        else:
            lm_start = date(today.year, today.month - 1, 1)
            lm_end = first_of_month.replace(day=1) - __import__("datetime").timedelta(days=1)

        income_last_month = (
            await db.execute(
                select(func.coalesce(func.sum(FinanceTransaction.amount), 0)).where(
                    FinanceTransaction.organization_id == org_id,
                    FinanceTransaction.app_code == APP_CODE,
                    FinanceTransaction.type == "income",
                    FinanceTransaction.date >= lm_start,
                    FinanceTransaction.date <= lm_end,
                )
            )
        ).scalar_one()

        return {
            "active_congregants": active_count,
            "inactive_congregants": inactive_count,
            "new_this_month": new_this_month,
            "income_this_month": Decimal(str(income_month)),
            "expenses_this_month": Decimal(str(expenses_month)),
            "net_this_month": Decimal(str(income_month)) - Decimal(str(expenses_month)),
            "income_last_month": Decimal(str(income_last_month)),
        }
