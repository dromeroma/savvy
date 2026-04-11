"""SavvyParking vehicle model."""

import uuid
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ParkingVehicle(BaseMixin, OrgMixin, Base):
    """A registered vehicle."""

    __tablename__ = "parking_vehicles"
    __table_args__ = (UniqueConstraint("organization_id", "plate", name="uq_parking_vehicles_org_plate"),)

    plate: Mapped[str] = mapped_column(String(20), nullable=False)
    vehicle_type: Mapped[str] = mapped_column(String(20), nullable=False, default="car")
    # car, motorcycle, truck, electric, bicycle
    brand: Mapped[str | None] = mapped_column(String(50), nullable=True)
    model: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(30), nullable=True)
    owner_person_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    subscription_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_subscriptions.id", ondelete="SET NULL"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # active, blacklisted
