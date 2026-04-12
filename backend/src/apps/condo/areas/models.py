"""SavvyCondo common areas and reservations."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CondoCommonArea(BaseMixin, OrgMixin, Base):
    __tablename__ = "condo_common_areas"

    property_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("condo_properties.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    area_type: Mapped[str] = mapped_column(String(30), nullable=False, default="social")
    # social, gym, pool, bbq, meeting_room, playground, terrace, other
    capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    requires_reservation: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    reservation_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # {"max_hours": 4, "advance_days": 7, "min_advance_hours": 24}
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class CondoReservation(BaseMixin, OrgMixin, Base):
    __tablename__ = "condo_reservations"

    area_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("condo_common_areas.id", ondelete="CASCADE"), nullable=False)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("condo_units.id", ondelete="SET NULL"), nullable=True)
    reserved_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    reserved_from: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    reserved_until: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    guests: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="confirmed")
    # confirmed, cancelled, completed
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
