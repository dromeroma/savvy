"""Pastoral models: member lifecycle, transfers, pastoral notes."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ChurchMemberLifecycle(BaseMixin, OrgMixin, Base):
    """Immutable history of a congregant's spiritual_status transitions."""

    __tablename__ = "church_member_lifecycle"

    congregant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_congregants.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    from_status: Mapped[str | None] = mapped_column(String(40), nullable=True)
    to_status: Mapped[str] = mapped_column(String(40), nullable=False)
    changed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    changed_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # This table is append-only; updated_at inherited from BaseMixin is unused.


class ChurchTransfer(BaseMixin, OrgMixin, Base):
    """Record of a congregant's transfer between organizational scopes."""

    __tablename__ = "church_transfers"

    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    from_scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    to_scope_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="CASCADE"), nullable=False,
    )
    transfer_date: Mapped[date] = mapped_column(Date, nullable=False)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    approved_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), default="completed", nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ChurchPastoralNote(BaseMixin, OrgMixin, Base):
    """Typed, access-controlled pastoral note about a person."""

    __tablename__ = "church_pastoral_notes"

    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    author_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    note_type: Mapped[str] = mapped_column(String(30), default="observation", nullable=False)
    visibility: Mapped[str] = mapped_column(String(20), default="pastor", nullable=False)
    title: Mapped[str | None] = mapped_column(String(200), nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
