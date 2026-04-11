"""SavvyCRM deal and stage history models."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CrmDeal(BaseMixin, OrgMixin, Base):
    """A deal/opportunity in the pipeline."""

    __tablename__ = "crm_deals"

    pipeline_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("crm_pipelines.id", ondelete="RESTRICT"), nullable=False)
    stage_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("crm_pipeline_stages.id", ondelete="RESTRICT"), nullable=False)
    contact_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("crm_contacts.id", ondelete="SET NULL"), nullable=True)
    company_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("crm_companies.id", ondelete="SET NULL"), nullable=True)
    lead_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("crm_leads.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False, default=0)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    probability: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    expected_close_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")
    # open, won, lost
    won_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lost_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    lost_reason: Mapped[str | None] = mapped_column(String(200), nullable=True)


class CrmDealStageHistory(BaseMixin, Base):
    """Tracks stage transitions for audit and analytics."""

    __tablename__ = "crm_deal_stage_history"

    deal_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("crm_deals.id", ondelete="CASCADE"), nullable=False)
    from_stage_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    to_stage_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    moved_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    moved_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
