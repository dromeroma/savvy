"""SavvyParking session and reservation models."""

import uuid
from datetime import datetime, date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ParkingSession(BaseMixin, OrgMixin, Base):
    """A parking session from entry to exit."""

    __tablename__ = "parking_sessions"

    location_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("parking_locations.id", ondelete="CASCADE"), nullable=False)
    spot_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_spots.id", ondelete="SET NULL"), nullable=True)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_vehicles.id", ondelete="SET NULL"), nullable=True)
    plate: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False, default="car")
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    pricing_rule_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_pricing_rules.id", ondelete="SET NULL"), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, paid, subscription, waived
    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    entry_method: Mapped[str] = mapped_column(String(20), nullable=False, default="manual")
    # manual, lpr, qr, rfid
    exit_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # active, completed, cancelled
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ParkingReservation(BaseMixin, OrgMixin, Base):
    """Pre-booking a parking spot."""

    __tablename__ = "parking_reservations"

    location_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("parking_locations.id", ondelete="CASCADE"), nullable=False)
    spot_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_spots.id", ondelete="SET NULL"), nullable=True)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_vehicles.id", ondelete="SET NULL"), nullable=True)
    plate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reserved_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reserved_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    # confirmed, checked_in, completed, cancelled, no_show
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
