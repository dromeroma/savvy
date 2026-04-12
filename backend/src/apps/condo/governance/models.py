"""SavvyCondo governance — assemblies and voting."""

import uuid
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CondoAssembly(BaseMixin, OrgMixin, Base):
    """An assembly/meeting with voting capabilities."""
    __tablename__ = "condo_assemblies"

    property_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("condo_properties.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    assembly_type: Mapped[str] = mapped_column(String(30), nullable=False, default="ordinary")
    # ordinary, extraordinary
    scheduled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    quorum_required: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=51.0)
    # Percentage of coefficient needed for quorum
    quorum_present: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    proposals: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    # [{"id": 1, "title": "...", "description": "..."}, ...]
    minutes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    # scheduled, in_progress, completed, cancelled


class CondoVote(BaseMixin, OrgMixin, Base):
    """A vote cast in an assembly."""
    __tablename__ = "condo_votes"
    __table_args__ = (UniqueConstraint("assembly_id", "unit_id", "proposal_index", name="uq_condo_votes_assembly_unit_proposal"),)

    assembly_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("condo_assemblies.id", ondelete="CASCADE"), nullable=False)
    unit_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("condo_units.id", ondelete="CASCADE"), nullable=False)
    proposal_index: Mapped[int] = mapped_column(Integer, nullable=False)
    vote: Mapped[str] = mapped_column(String(20), nullable=False)
    # yes, no, abstain
    coefficient_weight: Mapped[float] = mapped_column(Numeric(8, 6), nullable=False)
    voter_person_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
