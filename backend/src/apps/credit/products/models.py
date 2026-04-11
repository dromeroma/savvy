"""SavvyCredit product models — configurable credit product templates."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CreditProduct(BaseMixin, OrgMixin, Base):
    """A configurable credit product template.

    Each organization defines its own products with specific interest models,
    payment frequencies, fees, and rules.
    """

    __tablename__ = "credit_products"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_credit_products_org_code"),
    )

    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Interest configuration
    interest_type: Mapped[str] = mapped_column(String(30), nullable=False, default="declining_balance")
    # fixed, declining_balance, flat, compound
    interest_rate: Mapped[float] = mapped_column(Numeric(8, 4), nullable=False, default=0)
    # Rate value (e.g., 2.5 = 2.5%)
    interest_rate_period: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    # monthly, annual, daily

    # Amortization method
    amortization_method: Mapped[str] = mapped_column(String(20), nullable=False, default="french")
    # french (equal payments), german (equal principal), flat, bullet (interest-only + balloon)

    # Term configuration
    payment_frequency: Mapped[str] = mapped_column(String(20), nullable=False, default="monthly")
    # weekly, biweekly, monthly, quarterly, custom
    term_min: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    term_max: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    # Min/max number of installments

    # Amount limits
    amount_min: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    amount_max: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=999999999)

    # Grace period
    grace_period_days: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    # Late fee configuration
    late_fee_type: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    # none, percentage, fixed
    late_fee_value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)

    # Payment allocation method
    payment_allocation: Mapped[str] = mapped_column(String(20), nullable=False, default="interest_first")
    # interest_first, principal_first, proportional

    # Origination fee
    origination_fee_type: Mapped[str] = mapped_column(String(20), nullable=False, default="none")
    # none, percentage, fixed
    origination_fee_value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)

    # Requirements
    requires_guarantor: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    max_guarantors: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    # Flexible settings (JSONB for future extensibility)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # active, inactive, archived

    fees: Mapped[list["CreditProductFee"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin",
    )


class CreditProductFee(BaseMixin, Base):
    """Additional fees for a credit product (insurance, admin, etc.)."""

    __tablename__ = "credit_product_fees"

    product_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("credit_products.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    fee_type: Mapped[str] = mapped_column(String(20), nullable=False, default="fixed")
    # percentage, fixed
    value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False)
    applies_to: Mapped[str] = mapped_column(String(20), nullable=False, default="disbursement")
    # disbursement, monthly, annual
    is_required: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    product: Mapped[CreditProduct] = relationship(back_populates="fees")
