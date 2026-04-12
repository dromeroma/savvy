"""SavvyPOS sales models — transactions and line items."""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PosSale(BaseMixin, OrgMixin, Base):
    """A sale transaction."""
    __tablename__ = "pos_sales"

    sale_number: Mapped[str] = mapped_column(String(30), nullable=False)
    location_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pos_locations.id", ondelete="RESTRICT"), nullable=False)
    register_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("pos_cash_registers.id", ondelete="SET NULL"), nullable=True)
    customer_person_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    cashier_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)

    subtotal: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    discount_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)

    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, default="cash")
    # cash, card, bank_transfer, credit, mixed
    payment_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    pay_transaction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    # Link to pay_transactions

    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    # draft, completed, voided, refunded

    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    lines: Mapped[list["PosSaleLine"]] = relationship(
        back_populates="sale", cascade="all, delete-orphan", lazy="selectin",
    )


class PosSaleLine(BaseMixin, Base):
    """A line item in a sale."""
    __tablename__ = "pos_sale_lines"

    sale_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pos_sales.id", ondelete="CASCADE"), nullable=False)
    product_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pos_products.id", ondelete="RESTRICT"), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("pos_product_variants.id", ondelete="SET NULL"), nullable=True)
    product_name: Mapped[str] = mapped_column(String(200), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    tax_rate: Mapped[float] = mapped_column(Numeric(6, 4), nullable=False, default=0)
    tax_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    line_total: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)

    sale: Mapped[PosSale] = relationship(back_populates="lines")
