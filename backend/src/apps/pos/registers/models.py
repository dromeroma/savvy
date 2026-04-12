"""SavvyPOS cash register model."""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PosCashRegister(BaseMixin, OrgMixin, Base):
    """A cash register session (opening/closing)."""
    __tablename__ = "pos_cash_registers"

    location_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pos_locations.id", ondelete="RESTRICT"), nullable=False)
    register_name: Mapped[str] = mapped_column(String(100), nullable=False)
    cashier_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    opening_balance: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    closing_balance: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    expected_balance: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    difference: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    # open, closed
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
