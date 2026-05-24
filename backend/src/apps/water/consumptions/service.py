"""Business logic for monthly meter readings."""

from __future__ import annotations

import uuid
from decimal import Decimal

from sqlalchemy import exists, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.consumptions.schemas import (
    ConsumptionCreate,
    ConsumptionListItem,
    ConsumptionUpdate,
)
from src.apps.water.models import (
    WaterConsumption,
    WaterInvoice,
    WaterMeter,
    WaterSubscriber,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


class ConsumptionsService:

    @staticmethod
    async def list_consumptions(
        db: AsyncSession,
        org_id: uuid.UUID,
        period_year: int | None = None,
        period_month: int | None = None,
        meter_id: uuid.UUID | None = None,
        subscriber_id: uuid.UUID | None = None,
        limit: int = 200,
        offset: int = 0,
    ) -> list[ConsumptionListItem]:
        invoice_exists = (
            select(WaterInvoice.id)
            .where(WaterInvoice.consumption_id == WaterConsumption.id)
            .exists()
        )
        stmt = (
            select(
                WaterConsumption.id,
                WaterConsumption.period_year,
                WaterConsumption.period_month,
                WaterConsumption.reading_date,
                WaterConsumption.previous_reading,
                WaterConsumption.current_reading,
                WaterConsumption.consumption_cubic,
                WaterConsumption.is_estimated,
                WaterConsumption.meter_id,
                WaterMeter.serial_number.label("meter_serial"),
                WaterConsumption.subscriber_id,
                WaterSubscriber.code.label("sub_code"),
                func.coalesce(
                    WaterSubscriber.business_name,
                    func.concat(
                        WaterSubscriber.first_name, " ",
                        func.coalesce(WaterSubscriber.last_name, ""),
                    ),
                ).label("sub_name"),
                invoice_exists.label("has_invoice"),
            )
            .join(WaterMeter, WaterMeter.id == WaterConsumption.meter_id)
            .join(WaterSubscriber, WaterSubscriber.id == WaterConsumption.subscriber_id)
            .where(WaterConsumption.organization_id == org_id)
            .order_by(
                WaterConsumption.period_year.desc(),
                WaterConsumption.period_month.desc(),
                WaterConsumption.reading_date.desc(),
                WaterSubscriber.code,
            )
            .limit(limit)
            .offset(offset)
        )
        if period_year is not None:
            stmt = stmt.where(WaterConsumption.period_year == period_year)
        if period_month is not None:
            stmt = stmt.where(WaterConsumption.period_month == period_month)
        if meter_id is not None:
            stmt = stmt.where(WaterConsumption.meter_id == meter_id)
        if subscriber_id is not None:
            stmt = stmt.where(WaterConsumption.subscriber_id == subscriber_id)

        rows = await db.execute(stmt)
        return [
            ConsumptionListItem(
                id=r[0], period_year=r[1], period_month=r[2], reading_date=r[3],
                previous_reading=r[4], current_reading=r[5], consumption_cubic=r[6],
                is_estimated=r[7], meter_id=r[8], meter_serial=r[9],
                subscriber_id=r[10], subscriber_code=r[11],
                subscriber_name=(r[12].strip() if r[12] else ""),
                has_invoice=bool(r[13]),
            )
            for r in rows.all()
        ]

    @staticmethod
    async def get_consumption(
        db: AsyncSession, org_id: uuid.UUID, cons_id: uuid.UUID,
    ) -> WaterConsumption:
        c = await db.scalar(
            select(WaterConsumption).where(
                WaterConsumption.id == cons_id,
                WaterConsumption.organization_id == org_id,
            )
        )
        if c is None:
            raise NotFoundError("Consumption reading not found.")
        return c

    @staticmethod
    async def create_consumption(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: ConsumptionCreate,
        recorded_by: uuid.UUID | None,
    ) -> WaterConsumption:
        # Validate meter
        meter = await db.scalar(
            select(WaterMeter).where(
                WaterMeter.id == data.meter_id,
                WaterMeter.organization_id == org_id,
            )
        )
        if meter is None:
            raise NotFoundError("Meter not found.")
        if meter.subscriber_id is None:
            raise ValidationError(
                "Cannot register a reading for a meter without a subscriber.",
            )

        # One reading per (meter, period)
        existing = await db.scalar(
            select(WaterConsumption).where(
                WaterConsumption.meter_id == meter.id,
                WaterConsumption.period_year == data.period_year,
                WaterConsumption.period_month == data.period_month,
            )
        )
        if existing is not None:
            raise ConflictError(
                f"A reading already exists for this meter in {data.period_year}-"
                f"{data.period_month:02d}.",
            )

        previous = Decimal(meter.last_reading or 0)
        current = Decimal(data.current_reading)
        if current < previous:
            raise ValidationError(
                f"La lectura actual ({current}) no puede ser menor a la lectura "
                f"anterior del medidor ({previous}).",
            )
        consumption = current - previous

        row = WaterConsumption(
            organization_id=org_id,
            meter_id=meter.id,
            subscriber_id=meter.subscriber_id,
            period_year=data.period_year,
            period_month=data.period_month,
            reading_date=data.reading_date,
            previous_reading=previous,
            current_reading=current,
            consumption_cubic=consumption,
            is_estimated=data.is_estimated,
            notes=data.notes,
            recorded_by=recorded_by,
        )
        db.add(row)

        # Advance the meter
        meter.last_reading = current
        meter.last_reading_date = data.reading_date

        await db.flush()
        await db.refresh(row)
        return row

    @staticmethod
    async def update_consumption(
        db: AsyncSession,
        org_id: uuid.UUID,
        cons_id: uuid.UUID,
        data: ConsumptionUpdate,
    ) -> WaterConsumption:
        c = await ConsumptionsService.get_consumption(db, org_id, cons_id)

        # Block edits if the reading already produced an invoice.
        invoiced = await db.scalar(
            select(WaterInvoice.id).where(WaterInvoice.consumption_id == c.id)
        )
        if invoiced is not None:
            raise ConflictError(
                "Esta lectura ya tiene una factura generada; no se puede modificar.",
            )

        update_data = data.model_dump(exclude_unset=True)
        if "current_reading" in update_data:
            new_current = Decimal(update_data["current_reading"])
            if new_current < Decimal(c.previous_reading):
                raise ValidationError(
                    "La lectura actual no puede ser menor a la lectura anterior.",
                )
            c.current_reading = new_current
            c.consumption_cubic = new_current - Decimal(c.previous_reading)
            # Also update the meter if this is the latest reading
            meter = await db.get(WaterMeter, c.meter_id)
            if meter and Decimal(meter.last_reading or 0) == Decimal(c.current_reading):
                meter.last_reading = new_current
        for k in ("reading_date", "is_estimated", "notes"):
            if k in update_data:
                setattr(c, k, update_data[k])

        await db.flush()
        await db.refresh(c)
        return c

    @staticmethod
    async def delete_consumption(
        db: AsyncSession, org_id: uuid.UUID, cons_id: uuid.UUID,
    ) -> None:
        c = await ConsumptionsService.get_consumption(db, org_id, cons_id)
        invoiced = await db.scalar(
            select(WaterInvoice.id).where(WaterInvoice.consumption_id == c.id)
        )
        if invoiced is not None:
            raise ConflictError(
                "No se puede eliminar una lectura con factura asociada. "
                "Anula la factura primero.",
            )
        await db.delete(c)
        await db.flush()
