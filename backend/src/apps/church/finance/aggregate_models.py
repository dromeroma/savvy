"""Aggregate offerings model — mass-input tithes/offerings per event.

An aggregate offering captures the "remainder tithes/offerings" collected
at a service/event that were not individually attributed to members.
Each aggregate row is mirrored into the shared finance_transactions
ledger via `finance_transaction_id`, so reports still see a single ledger.
"""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ChurchAggregateOffering(BaseMixin, OrgMixin, Base):
    """Aggregate (mass-input) offering tied to a church event."""

    __tablename__ = "church_aggregate_offerings"

    event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("church_events.id", ondelete="SET NULL"), nullable=True,
    )
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    offering_type: Mapped[str] = mapped_column(
        String(30), default="tithe", nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False)
    contributor_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    payment_method: Mapped[str] = mapped_column(
        String(30), default="cash", nullable=False,
    )
    collected_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    finance_transaction_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("finance_transactions.id", ondelete="SET NULL"), nullable=True,
    )
    created_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
