"""SavvyCredit restructuring model."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CreditRestructuring(BaseMixin, OrgMixin, Base):
    """Record of a loan restructuring (refinancing, rescheduling, settlement)."""

    __tablename__ = "credit_restructurings"

    original_loan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_loans.id", ondelete="RESTRICT"), nullable=False,
    )
    new_loan_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("credit_loans.id", ondelete="SET NULL"), nullable=True,
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False)
    # refinancing, rescheduling, settlement, write_off
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    original_balance: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    new_balance: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    effective_date: Mapped[date] = mapped_column(Date, nullable=False)
    terms: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # New terms applied: {new_rate, new_term, discount_amount, ...}
    approved_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
