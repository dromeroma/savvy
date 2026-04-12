"""SavvyCondo fee model."""

import uuid
from datetime import date
from sqlalchemy import Date, ForeignKey, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CondoFee(BaseMixin, OrgMixin, Base):
    """A monthly administration fee for a unit."""
    __tablename__ = "condo_fees"

    unit_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("condo_units.id", ondelete="CASCADE"), nullable=False)
    period: Mapped[str] = mapped_column(String(7), nullable=False)  # 2026-04
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    late_fee: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, paid, partial, overdue
    description: Mapped[str | None] = mapped_column(String(200), nullable=True)
