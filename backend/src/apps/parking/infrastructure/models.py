"""SavvyParking infrastructure models — locations, zones, spots."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ParkingLocation(BaseMixin, OrgMixin, Base):
    """A parking facility / site."""

    __tablename__ = "parking_locations"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_parking_locations_org_code"),)

    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    longitude: Mapped[float | None] = mapped_column(Numeric(10, 7), nullable=True)
    total_capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_occupancy: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    operating_hours: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # {"mon": {"open": "06:00", "close": "22:00"}, "sat": {...}, "24h": true}
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class ParkingZone(BaseMixin, OrgMixin, Base):
    """A zone within a location (level, sector, area)."""

    __tablename__ = "parking_zones"

    location_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("parking_locations.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    zone_type: Mapped[str] = mapped_column(String(30), nullable=False, default="general")
    # general, vip, handicapped, motorcycle, electric, reserved
    level: Mapped[str | None] = mapped_column(String(20), nullable=True)  # B1, B2, P1, P2
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    current_occupancy: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class ParkingSpot(BaseMixin, OrgMixin, Base):
    """An individual parking spot."""

    __tablename__ = "parking_spots"
    __table_args__ = (UniqueConstraint("zone_id", "code", name="uq_parking_spots_zone_code"),)

    zone_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("parking_zones.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)  # A-001, B1-015
    spot_type: Mapped[str] = mapped_column(String(20), nullable=False, default="car")
    # car, motorcycle, truck, electric, handicapped
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="available")
    # available, occupied, reserved, maintenance, out_of_service
    has_sensor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    has_charger: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
