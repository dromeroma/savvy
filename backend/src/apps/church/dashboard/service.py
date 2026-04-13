"""Church dashboard KPIs service."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.congregants.models import ChurchCongregant
from src.modules.finance.models import FinanceTransaction
from src.modules.groups.models import OrganizationalScope
from src.modules.people.models import Person

APP_CODE = "church"


async def _descendant_scope_ids(
    db: AsyncSession, org_id: uuid.UUID, root_id: uuid.UUID,
) -> list[uuid.UUID]:
    """Return `root_id` plus all its descendant scope ids via recursive CTE."""
    cte = (
        select(OrganizationalScope.id, OrganizationalScope.parent_id)
        .where(
            OrganizationalScope.organization_id == org_id,
            OrganizationalScope.id == root_id,
        )
        .cte(name="scope_tree", recursive=True)
    )
    alias = cte.alias()
    cte = cte.union_all(
        select(OrganizationalScope.id, OrganizationalScope.parent_id)
        .where(
            OrganizationalScope.organization_id == org_id,
            OrganizationalScope.parent_id == alias.c.id,
        )
    )
    result = await db.execute(select(cte.c.id))
    return [row[0] for row in result.all()]


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
            lm_end = first_of_month - timedelta(days=1)

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

    # ------------------------------------------------------------------
    # Multi-level analytics (v2)
    # ------------------------------------------------------------------

    @staticmethod
    async def get_analytics(
        db: AsyncSession,
        org_id: uuid.UUID,
        scope_id: uuid.UUID | None = None,
    ) -> dict:
        """Return segmentation + growth analytics, optionally scoped to a subtree.

        If `scope_id` is provided, results are filtered to that scope and all
        its descendants. Otherwise, analytics cover the whole organization.
        """
        scope_filter = None
        if scope_id:
            scope_ids = await _descendant_scope_ids(db, org_id, scope_id)
            if scope_ids:
                scope_filter = ChurchCongregant.scope_id.in_(scope_ids)

        # Base where (org + scope + active only)
        base_where = [
            ChurchCongregant.organization_id == org_id,
            Person.deleted_at.is_(None),
        ]
        if scope_filter is not None:
            base_where.append(scope_filter)

        # Segmentation by gender
        gender_rows = await db.execute(
            select(
                func.coalesce(Person.gender, "unknown").label("gender"),
                func.count(ChurchCongregant.id),
            )
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(*base_where)
            .group_by(Person.gender)
        )
        by_gender = {row[0]: row[1] for row in gender_rows.all()}

        # Age bucket via case
        today = date.today()
        age_expr = func.extract("year", func.age(Person.date_of_birth))
        bucket = case(
            (age_expr < 13, "children"),
            (age_expr < 18, "teenagers"),
            (age_expr < 30, "youth"),
            (age_expr < 60, "adults"),
            else_="seniors",
        )
        age_rows = await db.execute(
            select(bucket.label("bucket"), func.count(ChurchCongregant.id))
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(*base_where, Person.date_of_birth.isnot(None))
            .group_by("bucket")
        )
        by_age = {row[0]: row[1] for row in age_rows.all()}

        # Spiritual status segmentation
        status_rows = await db.execute(
            select(
                func.coalesce(ChurchCongregant.spiritual_status, "unknown"),
                func.count(ChurchCongregant.id),
            )
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(*base_where)
            .group_by(ChurchCongregant.spiritual_status)
        )
        by_spiritual_status = {row[0]: row[1] for row in status_rows.all()}

        # Growth: last 6 months by membership_date
        six_months_ago = today.replace(day=1) - timedelta(days=180)
        growth_rows = await db.execute(
            select(
                func.date_trunc("month", ChurchCongregant.membership_date).label("m"),
                func.count(ChurchCongregant.id),
            )
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(
                *base_where,
                ChurchCongregant.membership_date.isnot(None),
                ChurchCongregant.membership_date >= six_months_ago,
            )
            .group_by("m")
            .order_by("m")
        )
        growth = [
            {"month": str(row[0].date()) if row[0] else None, "count": row[1]}
            for row in growth_rows.all()
        ]

        # Total active
        total_active = (
            await db.execute(
                select(func.count(ChurchCongregant.id))
                .join(Person, Person.id == ChurchCongregant.person_id)
                .where(*base_where, Person.status == "active")
            )
        ).scalar_one()

        # Finance segmentation by category (this year)
        year_start = date(today.year, 1, 1)
        fin_where = [
            FinanceTransaction.organization_id == org_id,
            FinanceTransaction.app_code == APP_CODE,
            FinanceTransaction.type == "income",
            FinanceTransaction.date >= year_start,
        ]
        if scope_filter is not None and scope_id:
            # Use scope_id on transaction if present, descendants
            fin_scope_ids = await _descendant_scope_ids(db, org_id, scope_id)
            if fin_scope_ids:
                fin_where.append(FinanceTransaction.scope_id.in_(fin_scope_ids))

        income_by_month_rows = await db.execute(
            select(
                func.date_trunc("month", FinanceTransaction.date).label("m"),
                func.coalesce(func.sum(FinanceTransaction.amount), 0),
            )
            .where(*fin_where)
            .group_by("m")
            .order_by("m")
        )
        income_by_month = [
            {
                "month": str(row[0].date()) if row[0] else None,
                "amount": float(row[1]),
            }
            for row in income_by_month_rows.all()
        ]

        return {
            "scope_id": str(scope_id) if scope_id else None,
            "total_active": total_active,
            "by_gender": by_gender,
            "by_age_bucket": by_age,
            "by_spiritual_status": by_spiritual_status,
            "growth_last_6_months": growth,
            "income_by_month": income_by_month,
        }

    # ------------------------------------------------------------------
    # Scope tree for dashboard selector
    # ------------------------------------------------------------------

    @staticmethod
    async def get_scope_tree(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[dict]:
        """Flat list of organizational scopes for the dashboard scope selector."""
        result = await db.execute(
            select(OrganizationalScope)
            .where(OrganizationalScope.organization_id == org_id)
            .order_by(OrganizationalScope.name)
        )
        return [
            {
                "id": str(s.id),
                "name": s.name,
                "code": s.code,
                "type": s.type,
                "parent_id": str(s.parent_id) if s.parent_id else None,
            }
            for s in result.scalars().all()
        ]
