"""SavvyPay payout model."""

import uuid
from datetime import date
from sqlalchemy import Date, ForeignKey, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PayPayout(BaseMixin, OrgMixin, Base):
    """A payout/withdrawal from the platform to a merchant/user."""

    __tablename__ = "pay_payouts"

    wallet_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pay_wallets.id", ondelete="RESTRICT"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    net_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    method: Mapped[str] = mapped_column(String(30), nullable=False, default="bank_transfer")
    # bank_transfer, check, cash, mobile_payment
    bank_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # {bank_name, account_number, account_type} — no sensitive data
    scheduled_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    executed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, processing, executed, failed, cancelled
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(100), nullable=True, unique=True)
