"""Visitor tracking model for SavvyChurch."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base


class ChurchVisitor(Base):
    """Tracks visitors to church services."""

    __tablename__ = "church_visitors"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    visit_date: Mapped[date] = mapped_column(Date, nullable=False)
    how_found: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(30), default="new", nullable=False)
    converted_person_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
