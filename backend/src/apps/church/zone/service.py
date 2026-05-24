"""Aggregate-only cross-org service for zone leaders."""

from __future__ import annotations

import uuid
from datetime import date, timedelta
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.congregants.models import ChurchCongregant
from src.apps.church.events.models import ChurchEvent
from src.apps.church.visitors.models import ChurchVisitor
from src.apps.church.zone.schemas import (
    ChurchMetrics,
    ZoneChurch,
    ZoneLeadership,
    ZoneOverviewResponse,
)
from src.core.exceptions import ForbiddenError, NotFoundError
from src.modules.church_hierarchy.models import (
    ChurchDenomination,
    ChurchZone,
    ChurchZoneLeader,
)
from src.modules.finance.models import FinanceTransaction
from src.modules.organization.models import Organization
from src.modules.people.models import Person


APP_CODE = "church"


class ZoneOverviewService:
    """Returns cross-org aggregate metrics for a zone leader."""

    @staticmethod
    async def get_overview(
        db: AsyncSession,
        user_id: uuid.UUID,
        user_org_id: uuid.UUID | None,
        zone_id: uuid.UUID | None,
        is_super_admin: bool,
    ) -> ZoneOverviewResponse:
        # 1) Resolve the set of zones the caller may inspect.
        if is_super_admin:
            zones = await ZoneOverviewService._all_zones(db)
        else:
            zones = await ZoneOverviewService._zones_for_user(db, user_id)
            if not zones:
                raise ForbiddenError("You are not a leader of any zone.")

        # 2) Pick the active zone.
        selected: ZoneLeadership | None = None
        if zone_id is not None:
            selected = next((z for z in zones if z.id == zone_id), None)
            if selected is None:
                raise ForbiddenError("You are not a leader of the requested zone.")
        elif zones:
            selected = zones[0]

        # 3) Build the church list for the selected zone.
        churches: list[ZoneChurch] = []
        if selected is not None:
            churches = await ZoneOverviewService._churches_with_metrics(
                db, selected.id, user_org_id,
            )

        return ZoneOverviewResponse(
            available_zones=zones,
            selected_zone=selected,
            churches=churches,
        )

    # ------------------------------------------------------------------
    # Zone resolution helpers
    # ------------------------------------------------------------------
    @staticmethod
    async def _zones_for_user(
        db: AsyncSession, user_id: uuid.UUID,
    ) -> list[ZoneLeadership]:
        rows = await db.execute(
            select(
                ChurchZone.id,
                ChurchZone.number,
                ChurchZone.name,
                ChurchDenomination.name.label("denom"),
                ChurchZoneLeader.role,
            )
            .join(ChurchZoneLeader, ChurchZoneLeader.zone_id == ChurchZone.id)
            .join(ChurchDenomination, ChurchDenomination.id == ChurchZone.denomination_id)
            .where(ChurchZoneLeader.user_id == user_id)
            .order_by(ChurchZone.number)
        )
        return [
            ZoneLeadership(
                id=r[0], number=r[1], name=r[2],
                denomination_name=r[3], role=r[4],
            )
            for r in rows.all()
        ]

    @staticmethod
    async def _all_zones(db: AsyncSession) -> list[ZoneLeadership]:
        """Super admin sees every zone (role label is 'super_admin')."""
        rows = await db.execute(
            select(
                ChurchZone.id,
                ChurchZone.number,
                ChurchZone.name,
                ChurchDenomination.name.label("denom"),
            )
            .join(ChurchDenomination, ChurchDenomination.id == ChurchZone.denomination_id)
            .order_by(ChurchDenomination.name, ChurchZone.number)
        )
        return [
            ZoneLeadership(
                id=r[0], number=r[1], name=r[2],
                denomination_name=r[3], role="super_admin",
            )
            for r in rows.all()
        ]

    # ------------------------------------------------------------------
    # Aggregate metrics
    # ------------------------------------------------------------------
    @staticmethod
    async def _churches_with_metrics(
        db: AsyncSession,
        zone_id: uuid.UUID,
        my_org_id: uuid.UUID | None,
    ) -> list[ZoneChurch]:
        today = date.today()
        first_of_month = today.replace(day=1)
        thirty_days_ago = today - timedelta(days=30)

        orgs = (
            await db.execute(
                select(Organization)
                .where(
                    Organization.zone_id == zone_id,
                    Organization.deleted_at.is_(None),
                )
                .order_by(Organization.name)
            )
        ).scalars().all()
        if not orgs:
            return []

        org_ids = [o.id for o in orgs]

        # Single-query aggregates per organization, indexed by org_id.
        active = dict((await db.execute(
            select(ChurchCongregant.organization_id, func.count(ChurchCongregant.id))
            .join(Person, Person.id == ChurchCongregant.person_id)
            .where(
                ChurchCongregant.organization_id.in_(org_ids),
                Person.status == "active",
            )
            .group_by(ChurchCongregant.organization_id)
        )).all())

        visitors = dict((await db.execute(
            select(ChurchVisitor.organization_id, func.count(ChurchVisitor.id))
            .where(
                ChurchVisitor.organization_id.in_(org_ids),
                ChurchVisitor.visit_date >= thirty_days_ago,
            )
            .group_by(ChurchVisitor.organization_id)
        )).all())

        events = dict((await db.execute(
            select(ChurchEvent.organization_id, func.count(ChurchEvent.id))
            .where(
                ChurchEvent.organization_id.in_(org_ids),
                ChurchEvent.date >= thirty_days_ago,
            )
            .group_by(ChurchEvent.organization_id)
        )).all())

        new_this_month = dict((await db.execute(
            select(ChurchCongregant.organization_id, func.count(ChurchCongregant.id))
            .where(
                ChurchCongregant.organization_id.in_(org_ids),
                func.date(ChurchCongregant.created_at) >= first_of_month,
            )
            .group_by(ChurchCongregant.organization_id)
        )).all())

        income = dict((await db.execute(
            select(
                FinanceTransaction.organization_id,
                func.coalesce(func.sum(FinanceTransaction.amount), 0),
            )
            .where(
                FinanceTransaction.organization_id.in_(org_ids),
                FinanceTransaction.app_code == APP_CODE,
                FinanceTransaction.type == "income",
                FinanceTransaction.date >= first_of_month,
                FinanceTransaction.date <= today,
            )
            .group_by(FinanceTransaction.organization_id)
        )).all())

        return [
            ZoneChurch(
                id=org.id,
                name=org.name,
                slug=org.slug,
                is_mine=(my_org_id is not None and org.id == my_org_id),
                metrics=ChurchMetrics(
                    active_congregants=active.get(org.id, 0),
                    visitors_last_30d=visitors.get(org.id, 0),
                    events_last_30d=events.get(org.id, 0),
                    new_congregants_this_month=new_this_month.get(org.id, 0),
                    income_this_month=Decimal(str(income.get(org.id, 0))),
                ),
            )
            for org in orgs
        ]


zone_overview_service = ZoneOverviewService()
