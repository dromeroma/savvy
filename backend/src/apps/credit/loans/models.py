"""SavvyCredit loan models — loans, amortization schedules, disbursements."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CreditLoan(BaseMixin, OrgMixin, Base):
    """An active loan with balances and lifecycle state."""

    __tablename__ = "credit_loans"

    borrower_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_borrowers.id", ondelete="RESTRICT"), nullable=False,
    )
    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_products.id", ondelete="RESTRICT"), nullable=False,
    )
    application_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("credit_applications.id", ondelete="SET NULL"), nullable=True,
    )
    loan_number: Mapped[str] = mapped_column(String(30), nullable=False)

    # Core terms (snapshot from product at origination time)
    principal: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    interest_rate: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False)
    interest_type: Mapped[str] = mapped_column(String(30), nullable=False)
    amortization_method: Mapped[str] = mapped_column(String(20), nullable=False)
    payment_frequency: Mapped[str] = mapped_column(String(20), nullable=False)
    total_installments: Mapped[int] = mapped_column(Integer, nullable=False)
    payment_allocation: Mapped[str] = mapped_column(String(20), nullable=False, default="interest_first")

    # Dates
    disbursement_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    first_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    maturity_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_payment_date: Mapped[date | None] = mapped_column(Date, nullable=True)

    # Running balances
    balance_principal: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    balance_interest: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    balance_penalties: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total_paid: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total_interest_paid: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)

    # Delinquency
    days_overdue: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    installments_overdue: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Status
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, active, current, delinquent, defaulted, paid_off, written_off, restructured

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class CreditAmortization(BaseMixin, Base):
    """Individual installment in the amortization schedule."""

    __tablename__ = "credit_amortization"

    loan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_loans.id", ondelete="CASCADE"), nullable=False,
    )
    installment_number: Mapped[int] = mapped_column(Integer, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    principal_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    interest_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    # Remaining principal after this installment

    # Payment tracking
    paid_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    paid_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, partial, paid, overdue


class CreditDisbursement(BaseMixin, OrgMixin, Base):
    """Record of a loan disbursement."""

    __tablename__ = "credit_disbursements"

    loan_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_loans.id", ondelete="CASCADE"), nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False, default="cash")
    # cash, bank_transfer, check, mobile_payment
    disbursement_date: Mapped[date] = mapped_column(Date, nullable=False)
    finance_transaction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
