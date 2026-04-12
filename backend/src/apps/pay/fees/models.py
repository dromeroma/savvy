"""SavvyPay fee configuration model."""

import uuid
from sqlalchemy import ForeignKey, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PayFeeRule(BaseMixin, OrgMixin, Base):
    """Configurable fee/commission rule."""

    __tablename__ = "pay_fee_rules"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    fee_type: Mapped[str] = mapped_column(String(20), nullable=False, default="percentage")
    # percentage, fixed, tiered
    percentage_value: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    # e.g., 2.5 = 2.5%
    fixed_value: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    min_fee: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    max_fee: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    applies_to: Mapped[str] = mapped_column(String(30), nullable=False, default="all")
    # all, payment, payout, subscription, transfer
    source_app: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # If set, only applies to transactions from this app
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Tiered rules: [{"up_to": 100000, "percentage": 3.0}, {"up_to": null, "percentage": 2.0}]
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
