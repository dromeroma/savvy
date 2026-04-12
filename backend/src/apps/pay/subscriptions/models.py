"""SavvyPay subscription model."""

import uuid
from datetime import date
from sqlalchemy import Boolean, Date, ForeignKey, Integer, Numeric, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PaySubscriptionPlan(BaseMixin, OrgMixin, Base):
    __tablename__ = "pay_subscription_plans"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    billing_cycle: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    # weekly, monthly, quarterly, annual
    trial_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    features: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)


class PaySubscription(BaseMixin, OrgMixin, Base):
    __tablename__ = "pay_subscriptions_active"

    plan_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pay_subscription_plans.id", ondelete="RESTRICT"), nullable=False)
    wallet_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("pay_wallets.id", ondelete="SET NULL"), nullable=True)
    subscriber_person_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # active, paused, cancelled, expired
    current_period_start: Mapped[date | None] = mapped_column(Date, nullable=True)
    current_period_end: Mapped[date | None] = mapped_column(Date, nullable=True)
    next_billing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    cancelled_at: Mapped[date | None] = mapped_column(Date, nullable=True)
