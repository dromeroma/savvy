"""Church finance models: income/expense categories and transactions."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ChurchIncomeCategory(Base):
    """Predefined income categories: tithe, offering, donation, other."""

    __tablename__ = "church_income_categories"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_church_income_cat_org_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("chart_of_accounts.id", ondelete="SET NULL"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


class ChurchIncome(BaseMixin, OrgMixin, Base):
    """A single income transaction (tithe, offering, donation, etc.)."""

    __tablename__ = "church_incomes"

    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_income_categories.id"), nullable=False,
    )
    church_member_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("church_members.id", ondelete="SET NULL"), nullable=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    fiscal_period_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("fiscal_periods.id"), nullable=True,
    )
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False,
    )


class ChurchExpenseCategory(Base):
    """Predefined expense categories: rent, utilities, salaries, etc."""

    __tablename__ = "church_expense_categories"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_church_expense_cat_org_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False)
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("chart_of_accounts.id", ondelete="SET NULL"), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


class ChurchExpense(BaseMixin, OrgMixin, Base):
    """A single expense transaction."""

    __tablename__ = "church_expenses"

    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_expense_categories.id"), nullable=False,
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    fiscal_period_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("fiscal_periods.id"), nullable=True,
    )
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("journal_entries.id", ondelete="SET NULL"), nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id"), nullable=False,
    )
