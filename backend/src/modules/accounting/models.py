"""SQLAlchemy 2.0 models for the double-entry accounting engine."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ChartOfAccounts(BaseMixin, OrgMixin, Base):
    """Chart of accounts with hierarchical structure per organization."""

    __tablename__ = "chart_of_accounts"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_chart_of_accounts_org_code"),
    )

    code: Mapped[str] = mapped_column(String(20), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("chart_of_accounts.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Self-referential relationship
    parent: Mapped["ChartOfAccounts | None"] = relationship(
        remote_side="ChartOfAccounts.id",
        lazy="selectin",
    )


class FiscalPeriod(Base):
    """Fiscal period (month) per organization. No updated_at column."""

    __tablename__ = "fiscal_periods"
    __table_args__ = (
        UniqueConstraint("organization_id", "year", "month", name="uq_fiscal_periods_org_year_month"),
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
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    month: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    closed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    closed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    journal_entries: Mapped[list["JournalEntry"]] = relationship(
        back_populates="fiscal_period", cascade="all, delete-orphan",
    )


class JournalEntry(Base):
    """Double-entry journal entry header. No updated_at column."""

    __tablename__ = "journal_entries"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    fiscal_period_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("fiscal_periods.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    entry_number: Mapped[int] = mapped_column(Integer, nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    description: Mapped[str] = mapped_column(String(500), nullable=False)
    source_app: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    reference_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="posted", nullable=False)
    created_by: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    fiscal_period: Mapped["FiscalPeriod"] = relationship(back_populates="journal_entries")
    lines: Mapped[list["JournalEntryLine"]] = relationship(
        back_populates="journal_entry", cascade="all, delete-orphan",
    )


class JournalEntryLine(Base):
    """Individual debit/credit line within a journal entry. No updated_at."""

    __tablename__ = "journal_entry_lines"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    journal_entry_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("journal_entries.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid,
        ForeignKey("chart_of_accounts.id", ondelete="CASCADE"),
        nullable=False,
    )
    debit: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    credit: Mapped[float] = mapped_column(Numeric(15, 2), default=0, nullable=False)
    description: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    journal_entry: Mapped["JournalEntry"] = relationship(back_populates="lines")
    account: Mapped["ChartOfAccounts"] = relationship(lazy="selectin")
