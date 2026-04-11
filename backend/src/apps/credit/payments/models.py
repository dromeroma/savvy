"""SavvyCredit payment and penalty models."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CreditPayment(BaseMixin, OrgMixin, Base):
    """A payment received for a loan."""

    __tablename__ = "credit_payments"

    loan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_loans.id", ondelete="CASCADE"), nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    principal_applied: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    interest_applied: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    penalty_applied: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    payment_date: Mapped[date] = mapped_column(Date, nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False, default="cash")
    finance_transaction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class CreditPenalty(BaseMixin, OrgMixin, Base):
    """A penalty generated due to delinquency."""

    __tablename__ = "credit_penalties"

    loan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_loans.id", ondelete="CASCADE"), nullable=False,
    )
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="late_fee")
    # late_fee, overdue_interest, collection_fee
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    applied_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, paid, waived
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
