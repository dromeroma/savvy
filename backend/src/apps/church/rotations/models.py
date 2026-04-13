"""Rotation models: definitions and per-event assignments."""

import uuid
from datetime import date

from sqlalchemy import Boolean, Date, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ChurchRotation(BaseMixin, OrgMixin, Base):
    """A named rotation (ushers, worship, cleaning)."""

    __tablename__ = "church_rotations"

    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    rotation_type: Mapped[str] = mapped_column(
        String(40), default="ushers", nullable=False,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    frequency: Mapped[str] = mapped_column(String(20), default="weekly", nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)


class ChurchRotationAssignment(BaseMixin, OrgMixin, Base):
    """One person's assignment on a rotation for a given event or date."""

    __tablename__ = "church_rotation_assignments"

    rotation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_rotations.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    event_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("church_events.id", ondelete="SET NULL"), nullable=True,
    )
    assignment_date: Mapped[date] = mapped_column(Date, nullable=False)
    role: Mapped[str | None] = mapped_column(String(60), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="scheduled", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
