"""SQLAlchemy models for church denominations, zones, and zone leaders."""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin


class ChurchDenomination(BaseMixin, Base):
    """Religious denomination (e.g. MMM). System rows have created_by_org_id=NULL
    and are visible to everyone; org-created rows are private to that org."""

    __tablename__ = "church_denominations"

    code: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    is_system: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_by_org_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), nullable=True,
    )

    zones: Mapped[list[ChurchZone]] = relationship(
        "ChurchZone", back_populates="denomination", cascade="all, delete-orphan",
    )


class ChurchZone(BaseMixin, Base):
    """Zone inside a denomination (e.g. MMM Zone 73 = Lorica)."""

    __tablename__ = "church_zones"
    __table_args__ = (
        UniqueConstraint("denomination_id", "number", name="uq_church_zone_denom_number"),
    )

    denomination_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_denominations.id", ondelete="CASCADE"),
        index=True, nullable=False,
    )
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    denomination: Mapped[ChurchDenomination] = relationship(back_populates="zones")
    leaders: Mapped[list[ChurchZoneLeader]] = relationship(
        "ChurchZoneLeader", back_populates="zone", cascade="all, delete-orphan",
    )


class ChurchZoneLeader(BaseMixin, Base):
    """Presbitero or lider of a zone. Grants cross-org read access to other
    churches in the same zone (aggregate metrics only by default)."""

    __tablename__ = "church_zone_leaders"
    __table_args__ = (
        UniqueConstraint("user_id", "zone_id", name="uq_church_zone_leader"),
        CheckConstraint(
            "role IN ('presbitero', 'lider')", name="chk_zone_leader_role",
        ),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("users.id", ondelete="CASCADE"), nullable=False,
    )
    zone_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_zones.id", ondelete="CASCADE"), nullable=False,
    )
    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="SET NULL"), nullable=True,
    )
    role: Mapped[str] = mapped_column(String(50), default="presbitero", nullable=False)
    assigned_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    zone: Mapped[ChurchZone] = relationship(back_populates="leaders")
