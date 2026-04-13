"""Church events/services model."""

import uuid
from datetime import date, datetime, time

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, Time, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ChurchEvent(Base):
    """A church service, event, or activity."""

    __tablename__ = "church_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # service, event, campaign, meeting
    event_category: Mapped[str | None] = mapped_column(String(40), nullable=True)
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    end_time: Mapped[time | None] = mapped_column(Time, nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_recurring: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    expected_attendance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="scheduled", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
