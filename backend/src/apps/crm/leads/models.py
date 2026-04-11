"""SavvyCRM lead model."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CrmLead(BaseMixin, OrgMixin, Base):
    """A lead/prospect before conversion to deal."""

    __tablename__ = "crm_leads"

    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("crm_contacts.id", ondelete="CASCADE"), nullable=False,
    )
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="new")
    # new, contacted, qualified, unqualified, converted, lost
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    converted_deal_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("crm_deals.id", ondelete="SET NULL"), nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
