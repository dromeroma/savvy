"""SavvyParking additional services models."""

import uuid
from sqlalchemy import ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ParkingServiceType(BaseMixin, OrgMixin, Base):
    """A service offered (car wash, valet, etc.)."""

    __tablename__ = "parking_services"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    duration_minutes: Mapped[int | None] = mapped_column(Numeric(5, 0), nullable=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="wash")
    # wash, valet, detailing, tire, other
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class ParkingServiceOrder(BaseMixin, OrgMixin, Base):
    """An order for a service linked to a session."""

    __tablename__ = "parking_service_orders"

    session_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_sessions.id", ondelete="SET NULL"), nullable=True)
    vehicle_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("parking_vehicles.id", ondelete="SET NULL"), nullable=True)
    service_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("parking_services.id", ondelete="CASCADE"), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, in_progress, completed, cancelled
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
