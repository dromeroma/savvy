"""SavvyCRM pipeline and stage models."""

import uuid

from sqlalchemy import Boolean, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CrmPipeline(BaseMixin, OrgMixin, Base):
    """A configurable sales pipeline."""

    __tablename__ = "crm_pipelines"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_crm_pipelines_org_name"),
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    deal_rot_days: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="COP")
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    stages: Mapped[list["CrmPipelineStage"]] = relationship(
        back_populates="pipeline", cascade="all, delete-orphan", lazy="selectin",
        order_by="CrmPipelineStage.sort_order",
    )


class CrmPipelineStage(BaseMixin, Base):
    """A stage within a pipeline."""

    __tablename__ = "crm_pipeline_stages"

    pipeline_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("crm_pipelines.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    probability: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 0-100 percentage
    color: Mapped[str | None] = mapped_column(String(10), nullable=True)
    is_won: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_lost: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    rules: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # {required_fields: [], auto_actions: []}

    pipeline: Mapped[CrmPipeline] = relationship(back_populates="stages")
