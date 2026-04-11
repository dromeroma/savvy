"""Business logic for parking sessions — entry, exit, pricing calculation."""

from __future__ import annotations
import uuid
from datetime import UTC, datetime
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError, ValidationError
from src.apps.parking.sessions.models import ParkingReservation, ParkingSession
from src.apps.parking.sessions.schemas import ReservationCreate, SessionEntryCreate, SessionExitCreate
from src.apps.parking.pricing.models import ParkingPricingRule
from src.apps.parking.infrastructure.models import ParkingLocation, ParkingSpot, ParkingZone
from src.apps.parking.vehicles.service import VehicleService
from src.apps.parking.vehicles.schemas import VehicleCreate


class SessionService:

    @staticmethod
    async def entry(db: AsyncSession, org_id: uuid.UUID, data: SessionEntryCreate) -> ParkingSession:
        """Register vehicle entry."""
        plate = data.plate.upper().strip()

        # Find or create vehicle
        vehicle = await VehicleService.find_by_plate(db, org_id, plate)
        if not vehicle:
            vehicle = await VehicleService.create_vehicle(db, org_id, VehicleCreate(plate=plate, vehicle_type=data.vehicle_type))

        # Update location occupancy
        loc_result = await db.execute(select(ParkingLocation).where(ParkingLocation.id == data.location_id))
        location = loc_result.scalar_one_or_none()
        if location:
            location.current_occupancy += 1

        # Update spot status
        if data.spot_id:
            spot_result = await db.execute(select(ParkingSpot).where(ParkingSpot.id == data.spot_id))
            spot = spot_result.scalar_one_or_none()
            if spot:
                spot.status = "occupied"

        session = ParkingSession(
            organization_id=org_id,
            location_id=data.location_id,
            spot_id=data.spot_id,
            vehicle_id=vehicle.id,
            plate=plate,
            vehicle_type=data.vehicle_type,
            entry_method=data.entry_method,
        )
        db.add(session)
        await db.flush()
        await db.refresh(session)
        return session

    @staticmethod
    async def exit(db: AsyncSession, org_id: uuid.UUID, session_id: uuid.UUID, data: SessionExitCreate) -> ParkingSession:
        """Register vehicle exit and calculate cost."""
        result = await db.execute(select(ParkingSession).where(ParkingSession.id == session_id, ParkingSession.organization_id == org_id))
        session = result.scalar_one_or_none()
        if session is None:
            raise NotFoundError("Session not found.")
        if session.status != "active":
            raise ValidationError("Session is not active.")

        now = datetime.now(UTC)
        session.exit_time = now
        duration = int((now - session.entry_time).total_seconds() / 60)
        session.duration_minutes = duration
        session.exit_method = data.payment_method
        session.payment_method = data.payment_method

        # Calculate cost
        amount = await SessionService._calculate_cost(db, org_id, session, duration)
        session.amount = float(amount)
        session.total = float(amount - Decimal(str(session.discount)))
        session.payment_status = "subscription" if data.payment_method == "subscription" else "paid"
        session.status = "completed"

        # Free spot
        if session.spot_id:
            spot_result = await db.execute(select(ParkingSpot).where(ParkingSpot.id == session.spot_id))
            spot = spot_result.scalar_one_or_none()
            if spot:
                spot.status = "available"

        # Update location occupancy
        loc_result = await db.execute(select(ParkingLocation).where(ParkingLocation.id == session.location_id))
        location = loc_result.scalar_one_or_none()
        if location:
            location.current_occupancy = max(0, location.current_occupancy - 1)

        await db.flush()
        await db.refresh(session)
        return session

    @staticmethod
    async def _calculate_cost(db: AsyncSession, org_id: uuid.UUID, session: ParkingSession, duration_minutes: int) -> Decimal:
        """Calculate cost using the applicable pricing rule."""
        # Find pricing rule
        rule_result = await db.execute(
            select(ParkingPricingRule).where(
                ParkingPricingRule.organization_id == org_id,
                ParkingPricingRule.vehicle_type == session.vehicle_type,
                ParkingPricingRule.status == "active",
            ).order_by(ParkingPricingRule.is_default.desc()).limit(1)
        )
        rule = rule_result.scalar_one_or_none()
        if rule is None:
            return Decimal("0")

        session.pricing_rule_id = rule.id
        billable = max(0, duration_minutes - rule.grace_minutes)
        rate = Decimal(str(rule.base_rate))
        min_charge = Decimal(str(rule.min_charge))

        if rule.pricing_model == "per_minute":
            amount = rate * billable
        elif rule.pricing_model == "per_hour":
            hours = Decimal(str(billable)) / 60
            amount = (rate * hours).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        elif rule.pricing_model == "flat_rate":
            amount = rate
        elif rule.pricing_model == "daily":
            days = max(1, (billable + 1439) // 1440)
            amount = rate * days
        else:
            amount = rate * billable

        amount = max(amount, min_charge)
        if rule.max_daily:
            amount = min(amount, Decimal(str(rule.max_daily)))

        return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    @staticmethod
    async def list_active(db: AsyncSession, org_id: uuid.UUID, location_id: uuid.UUID | None = None) -> list[ParkingSession]:
        q = select(ParkingSession).where(ParkingSession.organization_id == org_id, ParkingSession.status == "active")
        if location_id:
            q = q.where(ParkingSession.location_id == location_id)
        return list((await db.execute(q.order_by(ParkingSession.entry_time.desc()))).scalars().all())

    @staticmethod
    async def list_completed(db: AsyncSession, org_id: uuid.UUID, limit: int = 50) -> list[ParkingSession]:
        q = select(ParkingSession).where(ParkingSession.organization_id == org_id, ParkingSession.status == "completed").order_by(ParkingSession.exit_time.desc()).limit(limit)
        return list((await db.execute(q)).scalars().all())

    @staticmethod
    async def create_reservation(db: AsyncSession, org_id: uuid.UUID, data: ReservationCreate) -> ParkingReservation:
        res = ParkingReservation(organization_id=org_id, **data.model_dump())
        db.add(res)
        await db.flush()
        await db.refresh(res)
        return res

    @staticmethod
    async def list_reservations(db: AsyncSession, org_id: uuid.UUID) -> list[ParkingReservation]:
        return list((await db.execute(select(ParkingReservation).where(ParkingReservation.organization_id == org_id).order_by(ParkingReservation.reserved_from))).scalars().all())
