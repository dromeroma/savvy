"""Organization, Membership, Invitation, and BusinessTypeCatalog SQLAlchemy 2.0 models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin


class BusinessTypeCatalog(Base):
    """Catalog of business types selectable during signup (church, supermarket, ...).

    `default_app_code` controls which app gets auto-enabled when an org of this
    type is created. Stored as a soft reference (not a FK) to avoid coupling.
    """

    __tablename__ = "business_type_catalog"

    code: Mapped[str] = mapped_column(String(50), primary_key=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    default_app_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    icon: Mapped[str | None] = mapped_column(String(50), nullable=True)
    color: Mapped[str | None] = mapped_column(String(20), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


class Organization(BaseMixin, Base):
    """Tenant entity. Every multi-tenant row references this table."""

    __tablename__ = "organizations"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    # `type` is the org-kind: personal | business | platform | demo (enforced by DB CHECK).
    type: Mapped[str] = mapped_column(String(50), default="business")
    # `business_type` is the vertical (church, supermarket, restaurant, parking, condo, ...).
    # FK to business_type_catalog.code. Drives signup wizard + which app gets auto-enabled.
    business_type: Mapped[str | None] = mapped_column(
        String(50), ForeignKey("business_type_catalog.code"), nullable=True,
    )
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)
    # Church-specific (NULL when business_type != 'church')
    denomination_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("church_denominations.id", ondelete="SET NULL"), nullable=True,
    )
    zone_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("church_zones.id", ondelete="SET NULL"), nullable=True,
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    memberships: Mapped[list["Membership"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan",
    )
    invitations: Mapped[list["Invitation"]] = relationship(
        back_populates="organization", cascade="all, delete-orphan",
    )


class Membership(BaseMixin, Base):
    """Binds a user to an organization with a specific role."""

    __tablename__ = "memberships"
    __table_args__ = (
        UniqueConstraint("organization_id", "user_id", name="uq_memberships_org_user"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), default="member", nullable=False)
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="memberships")


class Invitation(Base):
    """Pending invitation for a user to join an organization.

    Does not use BaseMixin because the DB table lacks updated_at.
    """

    __tablename__ = "invitations"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), default="member")
    token: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    invited_by: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    status: Mapped[str] = mapped_column(String(50), default="pending")
    expires_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    organization: Mapped["Organization"] = relationship(back_populates="invitations")
