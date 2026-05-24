"""Business logic for water tariffs."""

from __future__ import annotations

import uuid
from datetime import date

from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.models import WaterTariff
from src.apps.water.tariffs.schemas import TariffCreate, TariffUpdate
from src.core.exceptions import ConflictError, NotFoundError


class TariffsService:

    @staticmethod
    async def list_tariffs(
        db: AsyncSession,
        org_id: uuid.UUID,
        active_only: bool = False,
    ) -> list[WaterTariff]:
        stmt = (
            select(WaterTariff)
            .where(WaterTariff.organization_id == org_id)
            .order_by(WaterTariff.subscriber_type, WaterTariff.stratum, WaterTariff.code)
        )
        if active_only:
            stmt = stmt.where(WaterTariff.is_active.is_(True))
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def get_tariff(
        db: AsyncSession, org_id: uuid.UUID, tariff_id: uuid.UUID,
    ) -> WaterTariff:
        t = await db.scalar(
            select(WaterTariff).where(
                WaterTariff.id == tariff_id,
                WaterTariff.organization_id == org_id,
            )
        )
        if t is None:
            raise NotFoundError("Tariff not found.")
        return t

    @staticmethod
    async def create_tariff(
        db: AsyncSession, org_id: uuid.UUID, data: TariffCreate,
    ) -> WaterTariff:
        existing = await db.scalar(
            select(WaterTariff).where(
                WaterTariff.organization_id == org_id,
                WaterTariff.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Already exists a tariff with code '{data.code}'.")
        t = WaterTariff(organization_id=org_id, **data.model_dump())
        db.add(t)
        await db.flush()
        await db.refresh(t)
        return t

    @staticmethod
    async def update_tariff(
        db: AsyncSession, org_id: uuid.UUID, tariff_id: uuid.UUID, data: TariffUpdate,
    ) -> WaterTariff:
        t = await TariffsService.get_tariff(db, org_id, tariff_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(t, k, v)
        await db.flush()
        await db.refresh(t)
        return t

    @staticmethod
    async def delete_tariff(
        db: AsyncSession, org_id: uuid.UUID, tariff_id: uuid.UUID,
    ) -> None:
        t = await TariffsService.get_tariff(db, org_id, tariff_id)
        await db.delete(t)
        await db.flush()

    # ------------------------------------------------------------------
    # Resolution: find the applicable tariff for a given subscriber on a date.
    # Called by the billing engine.
    # ------------------------------------------------------------------
    @staticmethod
    async def resolve_for_subscriber(
        db: AsyncSession,
        org_id: uuid.UUID,
        subscriber_type: str,
        stratum: int | None,
        on_date: date,
    ) -> WaterTariff | None:
        """Return the most specific active tariff that applies. Order:
        1. Same subscriber_type AND same stratum (exact match for residential)
        2. Same subscriber_type AND stratum IS NULL (catch-all for the type)
        """
        common = and_(
            WaterTariff.organization_id == org_id,
            WaterTariff.subscriber_type == subscriber_type,
            WaterTariff.is_active.is_(True),
            WaterTariff.valid_from <= on_date,
            or_(WaterTariff.valid_to.is_(None), WaterTariff.valid_to >= on_date),
        )
        if stratum is not None:
            exact = await db.scalar(
                select(WaterTariff)
                .where(common, WaterTariff.stratum == stratum)
                .order_by(WaterTariff.valid_from.desc())
                .limit(1)
            )
            if exact is not None:
                return exact
        # fallback: any tariff for the type with no stratum
        return await db.scalar(
            select(WaterTariff)
            .where(common, WaterTariff.stratum.is_(None))
            .order_by(WaterTariff.valid_from.desc())
            .limit(1)
        )
