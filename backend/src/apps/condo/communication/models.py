"""SavvyCondo announcements."""

import uuid
from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CondoAnnouncement(BaseMixin, OrgMixin, Base):
    __tablename__ = "condo_announcements"

    property_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("condo_properties.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False, default="general")
    # general, maintenance, financial, event, security, emergency
    priority: Mapped[str] = mapped_column(String(20), nullable=False, default="normal")
    # low, normal, high, urgent
    created_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="published")
