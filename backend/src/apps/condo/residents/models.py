"""SavvyCondo resident model + visitors."""

import uuid
from datetime import date, datetime
from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CondoResident(BaseMixin, OrgMixin, Base):
    """A resident (owner or tenant) linked to a unit."""
    __tablename__ = "condo_residents"
    __table_args__ = (UniqueConstraint("unit_id", "person_id", name="uq_condo_residents_unit_person"),)

    unit_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("condo_units.id", ondelete="CASCADE"), nullable=False)
    person_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    resident_type: Mapped[str] = mapped_column(String(20), nullable=False, default="owner")
    # owner, tenant, family_member, employee
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    move_in_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    move_out_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class CondoVisitor(BaseMixin, OrgMixin, Base):
    """Visitor entry log."""
    __tablename__ = "condo_visitors"

    unit_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("condo_units.id", ondelete="SET NULL"), nullable=True)
    visitor_name: Mapped[str] = mapped_column(String(200), nullable=False)
    document_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    vehicle_plate: Mapped[str | None] = mapped_column(String(20), nullable=True)
    purpose: Mapped[str | None] = mapped_column(String(100), nullable=True)
    entry_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    exit_time: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    authorized_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="inside")
    # inside, exited
