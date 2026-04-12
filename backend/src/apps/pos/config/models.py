"""SavvyPOS configuration models — taxes and discounts."""

import uuid
from datetime import date
from sqlalchemy import Boolean, Date, Numeric, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PosTax(BaseMixin, OrgMixin, Base):
    """Tax configuration."""
    __tablename__ = "pos_taxes"

    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    rate: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False)
    # 0.19 = 19%
    is_inclusive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class PosDiscount(BaseMixin, OrgMixin, Base):
    """Configurable discount/promotion."""
    __tablename__ = "pos_discounts"

    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    discount_type: Mapped[str] = mapped_column(String(20), nullable=False, default="percentage")
    # percentage, fixed
    value: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    min_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
