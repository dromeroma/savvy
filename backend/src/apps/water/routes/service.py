"""Business logic for water collection routes + collector views."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.models import (
    WaterInvoice,
    WaterRoute,
    WaterRouteSubscriber,
    WaterSubscriber,
)
from src.apps.water.routes.schemas import (
    CollectorRouteSummary,
    CollectorSubscriberItem,
    RouteAssignmentCreate,
    RouteAssignmentResponse,
    RouteCreate,
    RouteListItem,
    RouteUpdate,
)
from src.core.exceptions import ConflictError, NotFoundError
from src.modules.auth.models import User


class RoutesService:

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------
    @staticmethod
    async def list_routes(
        db: AsyncSession, org_id: uuid.UUID, active_only: bool = False,
    ) -> list[RouteListItem]:
        sub_count_sq = (
            select(
                WaterRouteSubscriber.route_id,
                func.count(WaterRouteSubscriber.id).label("n"),
            )
            .group_by(WaterRouteSubscriber.route_id)
            .subquery()
        )
        balance_sq = (
            select(
                WaterRouteSubscriber.route_id,
                func.coalesce(func.sum(WaterInvoice.balance), 0).label("bal"),
            )
            .join(WaterInvoice, WaterInvoice.subscriber_id == WaterRouteSubscriber.subscriber_id)
            .where(
                WaterInvoice.status.in_(("pending", "partial", "overdue")),
                WaterInvoice.balance > 0,
            )
            .group_by(WaterRouteSubscriber.route_id)
            .subquery()
        )
        stmt = (
            select(
                WaterRoute.id, WaterRoute.code, WaterRoute.name, WaterRoute.is_active,
                WaterRoute.collector_user_id,
                User.name.label("collector_name"),
                func.coalesce(sub_count_sq.c.n, 0).label("subs"),
                func.coalesce(balance_sq.c.bal, 0).label("bal"),
            )
            .outerjoin(User, User.id == WaterRoute.collector_user_id)
            .outerjoin(sub_count_sq, sub_count_sq.c.route_id == WaterRoute.id)
            .outerjoin(balance_sq, balance_sq.c.route_id == WaterRoute.id)
            .where(WaterRoute.organization_id == org_id)
            .order_by(WaterRoute.code)
        )
        if active_only:
            stmt = stmt.where(WaterRoute.is_active.is_(True))
        rows = await db.execute(stmt)
        return [
            RouteListItem(
                id=r[0], code=r[1], name=r[2], is_active=r[3],
                collector_user_id=r[4], collector_name=r[5],
                subscribers_count=int(r[6]), open_balance=Decimal(str(r[7])),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_route(
        db: AsyncSession, org_id: uuid.UUID, route_id: uuid.UUID,
    ) -> WaterRoute:
        r = await db.scalar(
            select(WaterRoute).where(
                WaterRoute.id == route_id,
                WaterRoute.organization_id == org_id,
            )
        )
        if r is None:
            raise NotFoundError("Route not found.")
        return r

    @staticmethod
    async def create_route(
        db: AsyncSession, org_id: uuid.UUID, data: RouteCreate,
    ) -> WaterRoute:
        existing = await db.scalar(
            select(WaterRoute).where(
                WaterRoute.organization_id == org_id,
                WaterRoute.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Already exists a route with code '{data.code}'.")
        r = WaterRoute(organization_id=org_id, **data.model_dump())
        db.add(r)
        await db.flush()
        await db.refresh(r)
        return r

    @staticmethod
    async def update_route(
        db: AsyncSession, org_id: uuid.UUID, route_id: uuid.UUID, data: RouteUpdate,
    ) -> WaterRoute:
        r = await RoutesService.get_route(db, org_id, route_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(r, k, v)
        await db.flush()
        await db.refresh(r)
        return r

    @staticmethod
    async def delete_route(
        db: AsyncSession, org_id: uuid.UUID, route_id: uuid.UUID,
    ) -> None:
        r = await RoutesService.get_route(db, org_id, route_id)
        await db.delete(r)
        await db.flush()

    # ------------------------------------------------------------------
    # Assignments
    # ------------------------------------------------------------------
    @staticmethod
    async def list_assignments(
        db: AsyncSession, org_id: uuid.UUID, route_id: uuid.UUID,
    ) -> list[RouteAssignmentResponse]:
        await RoutesService.get_route(db, org_id, route_id)
        rows = await db.execute(
            select(
                WaterRouteSubscriber.id, WaterRouteSubscriber.route_id,
                WaterRouteSubscriber.subscriber_id, WaterRouteSubscriber.sort_order,
                WaterSubscriber.code.label("sub_code"),
                func.coalesce(
                    WaterSubscriber.business_name,
                    func.concat(
                        WaterSubscriber.first_name, " ",
                        func.coalesce(WaterSubscriber.last_name, ""),
                    ),
                ).label("sub_name"),
            )
            .join(WaterSubscriber, WaterSubscriber.id == WaterRouteSubscriber.subscriber_id)
            .where(WaterRouteSubscriber.route_id == route_id)
            .order_by(WaterRouteSubscriber.sort_order, WaterSubscriber.code)
        )
        return [
            RouteAssignmentResponse(
                id=r[0], route_id=r[1], subscriber_id=r[2], sort_order=r[3],
                subscriber_code=r[4], subscriber_name=(r[5].strip() if r[5] else ""),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def assign(
        db: AsyncSession,
        org_id: uuid.UUID,
        route_id: uuid.UUID,
        data: RouteAssignmentCreate,
    ) -> RouteAssignmentResponse:
        route = await RoutesService.get_route(db, org_id, route_id)
        sub = await db.scalar(
            select(WaterSubscriber).where(
                WaterSubscriber.id == data.subscriber_id,
                WaterSubscriber.organization_id == org_id,
            )
        )
        if sub is None:
            raise NotFoundError("Subscriber not found.")
        existing = await db.scalar(
            select(WaterRouteSubscriber).where(
                WaterRouteSubscriber.route_id == route.id,
                WaterRouteSubscriber.subscriber_id == sub.id,
            )
        )
        if existing is not None:
            raise ConflictError("Subscriber already assigned to this route.")
        link = WaterRouteSubscriber(
            organization_id=org_id, route_id=route.id, subscriber_id=sub.id,
            sort_order=data.sort_order,
        )
        db.add(link)
        await db.flush()
        await db.refresh(link)
        return RouteAssignmentResponse(
            id=link.id, route_id=link.route_id, subscriber_id=link.subscriber_id,
            sort_order=link.sort_order, subscriber_code=sub.code,
            subscriber_name=(sub.business_name or f"{sub.first_name} {sub.last_name or ''}").strip(),
        )

    @staticmethod
    async def unassign(
        db: AsyncSession,
        org_id: uuid.UUID,
        route_id: uuid.UUID,
        subscriber_id: uuid.UUID,
    ) -> None:
        link = await db.scalar(
            select(WaterRouteSubscriber).where(
                WaterRouteSubscriber.route_id == route_id,
                WaterRouteSubscriber.subscriber_id == subscriber_id,
                WaterRouteSubscriber.organization_id == org_id,
            )
        )
        if link is None:
            raise NotFoundError("Assignment not found.")
        await db.delete(link)
        await db.flush()

    # ------------------------------------------------------------------
    # Collector mobile view
    # ------------------------------------------------------------------
    @staticmethod
    async def my_routes(
        db: AsyncSession, org_id: uuid.UUID, user_id: uuid.UUID,
    ) -> list[CollectorRouteSummary]:
        sub_count_sq = (
            select(
                WaterRouteSubscriber.route_id,
                func.count(WaterRouteSubscriber.id).label("n"),
            )
            .group_by(WaterRouteSubscriber.route_id)
            .subquery()
        )
        overdue_sq = (
            select(
                WaterRouteSubscriber.route_id,
                func.count(func.distinct(WaterInvoice.subscriber_id)).label("n"),
                func.coalesce(func.sum(WaterInvoice.balance), 0).label("bal"),
            )
            .join(WaterInvoice, WaterInvoice.subscriber_id == WaterRouteSubscriber.subscriber_id)
            .where(
                WaterInvoice.status.in_(("pending", "partial", "overdue")),
                WaterInvoice.balance > 0,
            )
            .group_by(WaterRouteSubscriber.route_id)
            .subquery()
        )
        rows = await db.execute(
            select(
                WaterRoute.id, WaterRoute.code, WaterRoute.name,
                func.coalesce(sub_count_sq.c.n, 0),
                func.coalesce(overdue_sq.c.n, 0),
                func.coalesce(overdue_sq.c.bal, 0),
            )
            .outerjoin(sub_count_sq, sub_count_sq.c.route_id == WaterRoute.id)
            .outerjoin(overdue_sq, overdue_sq.c.route_id == WaterRoute.id)
            .where(
                WaterRoute.organization_id == org_id,
                WaterRoute.collector_user_id == user_id,
                WaterRoute.is_active.is_(True),
            )
            .order_by(WaterRoute.code)
        )
        return [
            CollectorRouteSummary(
                route_id=r[0], route_code=r[1], route_name=r[2],
                subscribers_count=int(r[3]),
                overdue_count=int(r[4]),
                open_balance=Decimal(str(r[5])),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def route_collection_view(
        db: AsyncSession,
        org_id: uuid.UUID,
        route_id: uuid.UUID,
        user_id: uuid.UUID,
        require_collector: bool,
    ) -> list[CollectorSubscriberItem]:
        route = await db.scalar(
            select(WaterRoute).where(
                WaterRoute.id == route_id,
                WaterRoute.organization_id == org_id,
            )
        )
        if route is None:
            raise NotFoundError("Route not found.")
        if require_collector and route.collector_user_id != user_id:
            raise NotFoundError("Route not assigned to you.")

        today = date.today()
        balance_sq = (
            select(
                WaterInvoice.subscriber_id,
                func.coalesce(func.sum(WaterInvoice.balance), 0).label("bal"),
                func.count(WaterInvoice.id).filter(
                    WaterInvoice.status == "overdue"
                ).label("overdue_n"),
                func.min(WaterInvoice.due_date).filter(
                    WaterInvoice.status.in_(("overdue", "partial"))
                ).label("oldest"),
            )
            .where(
                WaterInvoice.organization_id == org_id,
                WaterInvoice.status.in_(("pending", "partial", "overdue")),
                WaterInvoice.balance > 0,
            )
            .group_by(WaterInvoice.subscriber_id)
            .subquery()
        )
        rows = await db.execute(
            select(
                WaterSubscriber.id, WaterSubscriber.code,
                func.coalesce(
                    WaterSubscriber.business_name,
                    func.concat(
                        WaterSubscriber.first_name, " ",
                        func.coalesce(WaterSubscriber.last_name, ""),
                    ),
                ).label("name"),
                WaterSubscriber.address, WaterSubscriber.mobile, WaterSubscriber.status,
                WaterRouteSubscriber.sort_order,
                func.coalesce(balance_sq.c.bal, 0),
                func.coalesce(balance_sq.c.overdue_n, 0),
                balance_sq.c.oldest,
            )
            .join(WaterRouteSubscriber, WaterRouteSubscriber.subscriber_id == WaterSubscriber.id)
            .outerjoin(balance_sq, balance_sq.c.subscriber_id == WaterSubscriber.id)
            .where(WaterRouteSubscriber.route_id == route.id)
            .order_by(WaterRouteSubscriber.sort_order, WaterSubscriber.code)
        )
        return [
            CollectorSubscriberItem(
                subscriber_id=r[0], code=r[1],
                name=(r[2].strip() if r[2] else ""),
                address=r[3], mobile=r[4], status=r[5], sort_order=r[6],
                open_balance=Decimal(str(r[7])),
                overdue_invoices=int(r[8]),
                oldest_due_date=r[9].isoformat() if r[9] else None,
            )
            for r in rows.all()
        ]
