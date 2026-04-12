"""SavvyPay transaction model — state machine for payment lifecycle.

State machine:
  pending → authorized → captured → settled
  pending → failed
  captured → refunded (partial or full)
  Any state → cancelled (before capture)
"""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Numeric, String, Text, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PayTransaction(BaseMixin, OrgMixin, Base):
    """A payment transaction with full lifecycle tracking."""

    __tablename__ = "pay_transactions"

    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    transaction_type: Mapped[str] = mapped_column(String(20), nullable=False, default="payment")
    # payment, refund, payout, transfer, subscription_charge
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    fee_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    net_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    # net_amount = amount - fee_amount

    # Parties
    payer_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("pay_accounts.id", ondelete="SET NULL"), nullable=True)
    payee_account_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("pay_accounts.id", ondelete="SET NULL"), nullable=True)
    payer_person_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    payee_person_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    # Payment method
    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # cash, card, bank_transfer, wallet, mobile_payment
    payment_method_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # {last4, brand, bank_name, etc.} — no sensitive data

    # State machine
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, authorized, captured, settled, failed, refunded, cancelled
    authorized_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    captured_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    settled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Refund tracking
    refunded_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)

    # Source traceability
    source_app: Mapped[str | None] = mapped_column(String(30), nullable=True)
    source_ref_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    source_ref_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    metadata_: Mapped[dict] = mapped_column("metadata", JSONB, nullable=False, default=dict)


class PayRefund(BaseMixin, OrgMixin, Base):
    """A refund against a transaction."""

    __tablename__ = "pay_refunds"

    transaction_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pay_transactions.id", ondelete="RESTRICT"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, processed, failed
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
    processed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
