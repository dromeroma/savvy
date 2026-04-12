"""SavvyCondo maintenance/PQR model."""

import uuid
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CondoMaintenance(BaseMixin, OrgMixin, Base):
    __tablename__ = "condo_maintenance"

    property_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("condo_properties.id", ondelete="CASCADE"), nullable=False)
    unit_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("condo_units.id", ondelete="SET NULL"), nullable=True)
    reported_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="general")
    # plumbing, electrical, structural, elevator, cleaning, security, general, other
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    # low, medium, high, urgent
    assigned_to: Mapped[str | None] = mapped_column(String(200), nullable=True)
    estimated_cost: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    actual_cost: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    # open, in_progress, completed, cancelled
    resolution: Mapped[str | None] = mapped_column(Text, nullable=True)
