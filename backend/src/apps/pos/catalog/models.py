"""SavvyPOS catalog models — locations, categories, products, variants."""

import uuid
from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class PosLocation(BaseMixin, OrgMixin, Base):
    """A physical location (branch/store)."""
    __tablename__ = "pos_locations"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_pos_locations_org_code"),)

    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class PosCategory(BaseMixin, OrgMixin, Base):
    """Product category with optional parent (hierarchy)."""
    __tablename__ = "pos_categories"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_pos_categories_org_code"),)

    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("pos_categories.id", ondelete="SET NULL"), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class PosProduct(BaseMixin, OrgMixin, Base):
    """A product in the catalog."""
    __tablename__ = "pos_products"
    __table_args__ = (UniqueConstraint("organization_id", "sku", name="uq_pos_products_org_sku"),)

    category_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("pos_categories.id", ondelete="SET NULL"), nullable=True)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    barcode: Mapped[str | None] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    product_type: Mapped[str] = mapped_column(String(20), nullable=False, default="simple")
    # simple, variant, bundle, service, recipe
    price: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    cost: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    tax_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("pos_taxes.id", ondelete="SET NULL"), nullable=True)
    tracks_inventory: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    variants: Mapped[list["PosProductVariant"]] = relationship(
        back_populates="product", cascade="all, delete-orphan", lazy="selectin",
    )


class PosProductVariant(BaseMixin, Base):
    """A variant of a product (size, color, etc.)."""
    __tablename__ = "pos_product_variants"
    __table_args__ = (UniqueConstraint("product_id", "sku", name="uq_pos_variants_product_sku"),)

    product_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("pos_products.id", ondelete="CASCADE"), nullable=False)
    sku: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    attributes: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # {"size": "M", "color": "red"}
    price_override: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    cost_override: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    barcode: Mapped[str | None] = mapped_column(String(50), nullable=True)

    product: Mapped[PosProduct] = relationship(back_populates="variants")
