"""SavvyPay Ledger — The single source of truth for all financial state.

Design principles:
1. IMMUTABLE: Ledger entries are never modified or deleted
2. BALANCED: Every journal must have SUM(debit) == SUM(credit)
3. DERIVED: All balances are computed from ledger entries, never stored directly
4. AUDITABLE: Every entry tracks who, when, why, and from which system

Account types:
- user_wallet: End-user/merchant available funds
- user_pending: Funds authorized but not yet settled
- user_reserved: Funds reserved (e.g., during payment auth)
- platform_fees: Platform commission account
- platform_clearing: Clearing account for settlement
- platform_reserve: Reserve/escrow account
- external_bank: Represents external bank movements
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PayAccount(BaseMixin, OrgMixin, Base):
    """An internal financial account in the ledger.

    Balances are NEVER stored here — they are derived from ledger entries.
    This table defines the account structure only.
    """

    __tablename__ = "pay_accounts"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_pay_accounts_org_code"),)

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    account_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # user_wallet, user_pending, user_reserved, platform_fees, platform_clearing,
    # platform_reserve, external_bank
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    owner_person_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    # NULL for platform accounts, set for user/merchant accounts
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class PayLedgerEntry(BaseMixin, Base):
    """An immutable double-entry ledger entry.

    CRITICAL INVARIANT: For any journal_id, SUM(debit) == SUM(credit).
    This is enforced in the LedgerEngine, not at the DB level.

    Entries are NEVER modified or deleted.
    """

    __tablename__ = "pay_ledger_entries"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    journal_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    # Groups related entries (debit + credit) into one logical journal
    account_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("pay_accounts.id", ondelete="RESTRICT"), nullable=False,
    )
    entry_type: Mapped[str] = mapped_column(String(10), nullable=False)
    # debit, credit
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    # Always positive — direction is determined by entry_type
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Traceability
    transaction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    # Links to pay_transactions for business context
    source_app: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # Which app originated this: pos, credit, parking, condo, health, etc.
    source_ref_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    # Audit
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    # Who initiated this action (user_id)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True)

    posted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


class PayEvent(BaseMixin, OrgMixin, Base):
    """Immutable financial event log — every action emits an event.

    Events are the basis for audit trails, webhooks, and replay.
    """

    __tablename__ = "pay_events"

    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    # payment.created, payment.captured, payment.settled, payment.refunded,
    # payout.created, payout.executed, wallet.funded, wallet.withdrawn,
    # subscription.charged, ledger.entry.created, fee.collected
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # transaction, payout, wallet, subscription, ledger
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Snapshot of the entity state at event time
    actor_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    source_app: Mapped[str | None] = mapped_column(String(30), nullable=True)


class PayIdempotencyKey(BaseMixin, Base):
    """Tracks idempotency keys to prevent duplicate operations."""

    __tablename__ = "pay_idempotency_keys"
    __table_args__ = (UniqueConstraint("key", name="uq_pay_idempotency_key"),)

    key: Mapped[str] = mapped_column(String(100), nullable=False)
    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    entity_type: Mapped[str] = mapped_column(String(30), nullable=False)
    entity_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    response_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
