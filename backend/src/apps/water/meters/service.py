"""Business logic for water meters."""

from __future__ import annotations

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.models import WaterMeter, WaterSubscriber
from src.apps.water.meters.schemas import (
    MeterCreate,
    MeterListItem,
    MeterUpdate,
)
from src.core.exceptions import ConflictError, NotFoundError


class MetersService:

    @staticmethod
    async def list_meters(
        db: AsyncSession,
        org_id: uuid.UUID,
        search: str | None = None,
        status: str | None = None,
        subscriber_id: uuid.UUID | None = None,
        unassigned_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> list[MeterListItem]:
        stmt = (
            select(
                WaterMeter.id,
                WaterMeter.serial_number,
                WaterMeter.brand,
                WaterMeter.model,
                WaterMeter.diameter,
                WaterMeter.status,
                WaterMeter.last_reading,
                WaterMeter.last_reading_date,
                WaterMeter.subscriber_id,
                WaterSubscriber.code.label("sub_code"),
                func.coalesce(
                    WaterSubscriber.business_name,
                    func.concat(
                        WaterSubscriber.first_name,
                        " ",
                        func.coalesce(WaterSubscriber.last_name, ""),
                    ),
                ).label("sub_name"),
            )
            .outerjoin(WaterSubscriber, WaterSubscriber.id == WaterMeter.subscriber_id)
            .where(WaterMeter.organization_id == org_id)
            .order_by(WaterMeter.serial_number)
            .limit(limit)
            .offset(offset)
        )
        if status:
            stmt = stmt.where(WaterMeter.status == status)
        if subscriber_id is not None:
            stmt = stmt.where(WaterMeter.subscriber_id == subscriber_id)
        if unassigned_only:
            stmt = stmt.where(WaterMeter.subscriber_id.is_(None))
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(WaterMeter.serial_number).like(like),
                    func.lower(func.coalesce(WaterMeter.brand, "")).like(like),
                    func.lower(func.coalesce(WaterMeter.model, "")).like(like),
                )
            )
        rows = await db.execute(stmt)
        return [
            MeterListItem(
                id=r[0], serial_number=r[1], brand=r[2], model=r[3], diameter=r[4],
                status=r[5], last_reading=r[6], last_reading_date=r[7],
                subscriber_id=r[8], subscriber_code=r[9],
                subscriber_name=(r[10].strip() if r[10] else None),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_meter(
        db: AsyncSession, org_id: uuid.UUID, meter_id: uuid.UUID,
    ) -> WaterMeter:
        m = await db.scalar(
            select(WaterMeter).where(
                WaterMeter.id == meter_id,
                WaterMeter.organization_id == org_id,
            )
        )
        if m is None:
            raise NotFoundError("Meter not found.")
        return m

    @staticmethod
    async def create_meter(
        db: AsyncSession, org_id: uuid.UUID, data: MeterCreate,
    ) -> WaterMeter:
        existing = await db.scalar(
            select(WaterMeter).where(
                WaterMeter.organization_id == org_id,
                WaterMeter.serial_number == data.serial_number,
            )
        )
        if existing is not None:
            raise ConflictError(
                f"Already exists a meter with serial '{data.serial_number}'.",
            )
        if data.subscriber_id is not None:
            await MetersService._validate_subscriber(db, org_id, data.subscriber_id)
        meter = WaterMeter(organization_id=org_id, **data.model_dump())
        db.add(meter)
        await db.flush()
        await db.refresh(meter)
        return meter

    @staticmethod
    async def update_meter(
        db: AsyncSession,
        org_id: uuid.UUID,
        meter_id: uuid.UUID,
        data: MeterUpdate,
    ) -> WaterMeter:
        m = await MetersService.get_meter(db, org_id, meter_id)
        update_data = data.model_dump(exclude_unset=True)
        if "subscriber_id" in update_data and update_data["subscriber_id"] is not None:
            await MetersService._validate_subscriber(
                db, org_id, update_data["subscriber_id"],
            )
        for k, v in update_data.items():
            setattr(m, k, v)
        await db.flush()
        await db.refresh(m)
        return m

    @staticmethod
    async def delete_meter(
        db: AsyncSession, org_id: uuid.UUID, meter_id: uuid.UUID,
    ) -> None:
        m = await MetersService.get_meter(db, org_id, meter_id)
        await db.delete(m)
        await db.flush()

    @staticmethod
    async def _validate_subscriber(
        db: AsyncSession, org_id: uuid.UUID, sub_id: uuid.UUID,
    ) -> None:
        sub = await db.scalar(
            select(WaterSubscriber.id).where(
                WaterSubscriber.id == sub_id,
                WaterSubscriber.organization_id == org_id,
            )
        )
        if sub is None:
            raise NotFoundError("Subscriber not found for this organization.")
