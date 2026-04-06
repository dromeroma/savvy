"""SQLAlchemy 2.0 models for the SavvyFinance module."""

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


class FinanceCategory(Base):
    """Income/expense category per organization and optional app.

    Does not use BaseMixin because the DB table lacks updated_at.
    """

    __tablename__ = "finance_categories"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "app_code", "code",
            name="uq_finance_categories_org_app_code",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    app_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)
    account_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("chart_of_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


class FinanceTransaction(BaseMixin, OrgMixin, Base):
    """Universal income/expense transaction shared by all apps."""

    __tablename__ = "finance_transactions"

    category_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("finance_categories.id", ondelete="CASCADE"),
        nullable=False,
    )
    type: Mapped[str] = mapped_column(String(10), nullable=False)
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("people.id", ondelete="SET NULL"),
        nullable=True,
    )
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    vendor: Mapped[str | None] = mapped_column(String(255), nullable=True)
    receipt_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    app_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("organizational_scopes.id", ondelete="SET NULL"),
        nullable=True,
    )
    fiscal_period_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("fiscal_periods.id", ondelete="SET NULL"),
        nullable=True,
    )
    journal_entry_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("journal_entries.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )


class FinancePaymentAccount(Base):
    """Maps a payment method to a chart-of-accounts entry per organization.

    Does not use BaseMixin because the DB table lacks updated_at.
    """

    __tablename__ = "finance_payment_accounts"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "payment_method",
            name="uq_finance_payment_accounts_org_method",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("chart_of_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
