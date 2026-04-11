"""SavvyCRM activity model."""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CrmActivity(BaseMixin, OrgMixin, Base):
    """Unified activity log: calls, meetings, emails, tasks, notes."""

    __tablename__ = "crm_activities"

    type: Mapped[str] = mapped_column(String(20), nullable=False)
    # call, meeting, email, task, note
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("crm_contacts.id", ondelete="SET NULL"), nullable=True)
    deal_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("crm_deals.id", ondelete="SET NULL"), nullable=True)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    completed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
