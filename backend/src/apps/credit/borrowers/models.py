"""SavvyCredit borrower models — extends People with credit-specific data."""

import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CreditBorrower(BaseMixin, OrgMixin, Base):
    """Credit-specific data for a person who borrows."""

    __tablename__ = "credit_borrowers"
    __table_args__ = (
        UniqueConstraint("organization_id", "person_id", name="uq_credit_borrowers_org_person"),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    credit_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    # Internal credit score (0-1000 or custom)
    credit_limit: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    risk_level: Mapped[str] = mapped_column(String(20), nullable=False, default="medium")
    # low, medium, high, very_high
    total_borrowed: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total_outstanding: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total_paid: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    active_loans: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completed_loans: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    defaulted_loans: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    employer: Mapped[str | None] = mapped_column(String(200), nullable=True)
    monthly_income: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # active, blocked, blacklisted


class CreditGuarantor(BaseMixin, OrgMixin, Base):
    """A guarantor/co-signer for a specific loan."""

    __tablename__ = "credit_guarantors"
    __table_args__ = (
        UniqueConstraint("loan_id", "person_id", name="uq_credit_guarantors_loan_person"),
    )

    loan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_loans.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    relationship: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # spouse, parent, sibling, friend, employer, other
    guarantee_amount: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
