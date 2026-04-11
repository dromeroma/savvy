"""SavvyEdu scheduling models — rooms and schedule blocks."""

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Time, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class EduRoom(BaseMixin, OrgMixin, Base):
    """A physical space (classroom, lab, auditorium)."""

    __tablename__ = "edu_rooms"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_edu_rooms_org_name"),
    )

    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    building: Mapped[str | None] = mapped_column(String(100), nullable=True)
    floor: Mapped[str | None] = mapped_column(String(20), nullable=True)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="classroom")  # classroom, lab, auditorium, virtual
    equipment: Mapped[dict | None] = mapped_column(JSONB, nullable=True)  # ["projector", "whiteboard", ...]
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class EduSchedule(BaseMixin, Base):
    """A time block for a section in a room."""

    __tablename__ = "edu_schedules"
    __table_args__ = (
        UniqueConstraint("section_id", "day_of_week", "start_time", name="uq_edu_schedules_section_day_time"),
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_sections.id", ondelete="CASCADE"), nullable=False,
    )
    room_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_rooms.id", ondelete="SET NULL"), nullable=True,
    )
    day_of_week: Mapped[int] = mapped_column(Integer, nullable=False)  # 0=Monday ... 6=Sunday
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "08:00"
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)    # "10:00"
