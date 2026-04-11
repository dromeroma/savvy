"""SavvyParking pricing and subscription models."""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ParkingPricingRule(BaseMixin, OrgMixin, Base):
    """Config-driven pricing rule."""

    __tablename__ = "parking_pricing_rules"

    location_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_locations.id", ondelete="SET NULL"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False, default="car")
    pricing_model: Mapped[str] = mapped_column(String(20), nullable=False, default="per_minute")
    # per_minute, per_hour, flat_rate, daily, dynamic
    base_rate: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    # Rate per unit (per minute, per hour, or flat amount)
    min_charge: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    max_daily: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    # Cap diario máximo
    grace_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=15)
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # {"night_rate": 50, "night_start": "22:00", "night_end": "06:00", "weekend_multiplier": 1.5}
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class ParkingSubscription(BaseMixin, OrgMixin, Base):
    """Monthly/annual subscription plan."""

    __tablename__ = "parking_subscriptions"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    plan_type: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    # monthly, quarterly, annual
    vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False, default="car")
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    location_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_locations.id", ondelete="SET NULL"), nullable=True)
    zone_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_zones.id", ondelete="SET NULL"), nullable=True)
    max_vehicles: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    includes_services: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    # ["wash_monthly", "valet"]
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
