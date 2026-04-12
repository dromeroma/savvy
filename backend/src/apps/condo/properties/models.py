"""SavvyCondo property and unit models."""

import uuid
from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CondoProperty(BaseMixin, OrgMixin, Base):
    """A building, tower, or residential complex."""

    __tablename__ = "condo_properties"
    __table_args__ = (UniqueConstraint("organization_id", "code", name="uq_condo_properties_org_code"),)

    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    property_type: Mapped[str] = mapped_column(String(30), nullable=False, default="residential")
    # residential, commercial, mixed, office
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    total_units: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    total_area_sqm: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    admin_fee_base: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    # Base monthly admin fee (applied per coefficient)
    late_fee_type: Mapped[str] = mapped_column(String(20), nullable=False, default="percentage")
    # percentage, fixed, none
    late_fee_value: Mapped[float] = mapped_column(Numeric(10, 4), nullable=False, default=0)
    grace_days: Mapped[int] = mapped_column(Integer, nullable=False, default=10)
    settings: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class CondoUnit(BaseMixin, OrgMixin, Base):
    """An individual unit (apartment, office, local)."""

    __tablename__ = "condo_units"
    __table_args__ = (UniqueConstraint("property_id", "code", name="uq_condo_units_prop_code"),)

    property_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("condo_properties.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str] = mapped_column(String(20), nullable=False)  # Apto 101, Ofc 302
    unit_type: Mapped[str] = mapped_column(String(20), nullable=False, default="apartment")
    # apartment, office, commercial, parking, storage
    floor: Mapped[str | None] = mapped_column(String(10), nullable=True)
    area_sqm: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    coefficient: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False, default=1.0)
    # Coeficiente de copropiedad (para distribuir cuotas)
    bedrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    bathrooms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    owner_person_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="occupied")
    # occupied, vacant, for_sale, for_rent
