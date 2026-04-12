"""SavvyPOS inventory models — stock per location + immutable movement history."""

import uuid
from datetime import datetime
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PosInventory(BaseMixin, OrgMixin, Base):
    """Current stock level per product per location.

    This is a materialized view for performance. The source of truth
    is pos_stock_movements (immutable audit trail).
    """
    __tablename__ = "pos_inventory"
    __table_args__ = (UniqueConstraint("product_id", "variant_id", "location_id", name="uq_pos_inventory_pvl"),)

    product_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pos_products.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("pos_product_variants.id", ondelete="CASCADE"), nullable=True)
    location_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pos_locations.id", ondelete="CASCADE"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False, default=0)
    min_stock: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False, default=0)
    max_stock: Mapped[float | None] = mapped_column(Numeric(15, 3), nullable=True)


class PosStockMovement(BaseMixin, OrgMixin, Base):
    """IMMUTABLE audit trail of all stock changes."""
    __tablename__ = "pos_stock_movements"

    product_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pos_products.id", ondelete="CASCADE"), nullable=False)
    variant_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("pos_product_variants.id", ondelete="SET NULL"), nullable=True)
    location_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pos_locations.id", ondelete="CASCADE"), nullable=False)
    movement_type: Mapped[str] = mapped_column(String(20), nullable=False)
    # purchase, sale, adjustment, transfer_in, transfer_out, return
    quantity: Mapped[float] = mapped_column(Numeric(15, 3), nullable=False)
    # Positive for in, negative for out
    unit_cost: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # sale, purchase_order, adjustment, transfer
    reference_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    performed_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
