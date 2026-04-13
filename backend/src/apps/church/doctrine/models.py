"""Doctrine sub-module models."""

import uuid
from datetime import date, time

from sqlalchemy import Boolean, Date, ForeignKey, Integer, String, Text, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ChurchDoctrineGroup(BaseMixin, OrgMixin, Base):
    """A doctrine / pre-baptism class."""

    __tablename__ = "church_doctrine_groups"

    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    name: Mapped[str] = mapped_column(String(150), nullable=False)
    teacher_person_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    meeting_day: Mapped[str | None] = mapped_column(String(20), nullable=True)
    meeting_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    max_students: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)


class ChurchDoctrineEnrollment(BaseMixin, OrgMixin, Base):
    """A student's enrollment into a doctrine group."""

    __tablename__ = "church_doctrine_enrollments"

    doctrine_group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_doctrine_groups.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    enrolled_at: Mapped[date] = mapped_column(Date, nullable=False)
    progress_pct: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    result: Mapped[str | None] = mapped_column(String(20), nullable=True)
    result_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class ChurchDoctrineAttendance(BaseMixin, OrgMixin, Base):
    """Per-session attendance record for a doctrine group."""

    __tablename__ = "church_doctrine_attendance"

    doctrine_group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_doctrine_groups.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    session_date: Mapped[date] = mapped_column(Date, nullable=False)
    present: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
