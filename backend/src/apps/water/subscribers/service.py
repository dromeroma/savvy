"""Business logic for water subscribers."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.models import WaterMeter, WaterSubscriber
from src.apps.water.subscribers.schemas import (
    SubscriberCreate,
    SubscriberListItem,
    SubscriberUpdate,
)
from src.core.exceptions import ConflictError, NotFoundError


class SubscribersService:

    @staticmethod
    async def list_subscribers(
        db: AsyncSession,
        org_id: uuid.UUID,
        search: str | None = None,
        status: str | None = None,
        subscriber_type: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[SubscriberListItem]:
        meter_count_sq = (
            select(
                WaterMeter.subscriber_id,
                func.count(WaterMeter.id).label("n"),
            )
            .where(WaterMeter.organization_id == org_id)
            .group_by(WaterMeter.subscriber_id)
            .subquery()
        )

        stmt = (
            select(
                WaterSubscriber.id,
                WaterSubscriber.code,
                WaterSubscriber.first_name,
                WaterSubscriber.last_name,
                WaterSubscriber.business_name,
                WaterSubscriber.document_number,
                WaterSubscriber.address,
                WaterSubscriber.neighborhood,
                WaterSubscriber.subscriber_type,
                WaterSubscriber.status,
                WaterSubscriber.stratum,
                func.coalesce(meter_count_sq.c.n, 0).label("meter_count"),
            )
            .outerjoin(meter_count_sq, meter_count_sq.c.subscriber_id == WaterSubscriber.id)
            .where(WaterSubscriber.organization_id == org_id)
            .order_by(WaterSubscriber.code)
            .limit(limit)
            .offset(offset)
        )
        if status:
            stmt = stmt.where(WaterSubscriber.status == status)
        if subscriber_type:
            stmt = stmt.where(WaterSubscriber.subscriber_type == subscriber_type)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(WaterSubscriber.code).like(like),
                    func.lower(WaterSubscriber.first_name).like(like),
                    func.lower(func.coalesce(WaterSubscriber.last_name, "")).like(like),
                    func.lower(func.coalesce(WaterSubscriber.business_name, "")).like(like),
                    func.lower(func.coalesce(WaterSubscriber.document_number, "")).like(like),
                )
            )

        rows = await db.execute(stmt)
        return [
            SubscriberListItem(
                id=r[0], code=r[1], first_name=r[2], last_name=r[3],
                business_name=r[4], document_number=r[5], address=r[6],
                neighborhood=r[7], subscriber_type=r[8], status=r[9],
                stratum=r[10], meter_count=int(r[11]),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_subscriber(
        db: AsyncSession, org_id: uuid.UUID, sub_id: uuid.UUID,
    ) -> WaterSubscriber:
        sub = await db.scalar(
            select(WaterSubscriber).where(
                WaterSubscriber.id == sub_id,
                WaterSubscriber.organization_id == org_id,
            )
        )
        if sub is None:
            raise NotFoundError("Subscriber not found.")
        return sub

    @staticmethod
    async def create_subscriber(
        db: AsyncSession, org_id: uuid.UUID, data: SubscriberCreate,
    ) -> WaterSubscriber:
        existing = await db.scalar(
            select(WaterSubscriber).where(
                WaterSubscriber.organization_id == org_id,
                WaterSubscriber.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Already exists a subscriber with code '{data.code}'.")
        sub = WaterSubscriber(organization_id=org_id, **data.model_dump())
        db.add(sub)
        await db.flush()
        await db.refresh(sub)
        return sub

    @staticmethod
    async def update_subscriber(
        db: AsyncSession,
        org_id: uuid.UUID,
        sub_id: uuid.UUID,
        data: SubscriberUpdate,
    ) -> WaterSubscriber:
        sub = await SubscribersService.get_subscriber(db, org_id, sub_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(sub, k, v)
        await db.flush()
        await db.refresh(sub)
        return sub

    @staticmethod
    async def delete_subscriber(
        db: AsyncSession, org_id: uuid.UUID, sub_id: uuid.UUID,
    ) -> None:
        sub = await SubscribersService.get_subscriber(db, org_id, sub_id)
        await db.delete(sub)
        await db.flush()
