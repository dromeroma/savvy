"""SavvyEdu configuration models — grading systems, grade scales,
academic period types, and evaluation templates.

These are configuration-driven: each institution defines its own
grading system, academic calendar, and evaluation model.
"""

import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, Uuid, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class EduGradingSystem(BaseMixin, OrgMixin, Base):
    """A configurable grading system (numeric, letter, percentage)."""

    __tablename__ = "edu_grading_systems"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False)  # numeric, letter, percentage
    scale_min: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=0)
    scale_max: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=100)
    passing_grade: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False, default=60)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    scales: Mapped[list["EduGradeScale"]] = relationship(
        back_populates="grading_system", cascade="all, delete-orphan", lazy="selectin",
    )


class EduGradeScale(BaseMixin, Base):
    """Individual scale entry within a grading system (e.g., A=90-100)."""

    __tablename__ = "edu_grade_scales"

    grading_system_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_grading_systems.id", ondelete="CASCADE"), nullable=False,
    )
    label: Mapped[str] = mapped_column(String(10), nullable=False)  # A, B, C or 5.0, 4.5
    min_value: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    max_value: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    gpa_value: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    is_passing: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    grading_system: Mapped[EduGradingSystem] = relationship(back_populates="scales")


class EduAcademicPeriodType(BaseMixin, OrgMixin, Base):
    """Academic calendar type (semester, trimester, quarter, annual, custom)."""

    __tablename__ = "edu_academic_period_types"

    code: Mapped[str] = mapped_column(String(30), nullable=False)  # semester, trimester, etc.
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    default_duration_weeks: Mapped[int] = mapped_column(Integer, nullable=False, default=16)


class EduEvaluationTemplate(BaseMixin, OrgMixin, Base):
    """Evaluation model template with weighted components.

    components is a JSONB array like:
    [{"name": "Parciales", "weight": 0.3, "type": "exam"},
     {"name": "Trabajos", "weight": 0.3, "type": "assignment"},
     {"name": "Final", "weight": 0.4, "type": "exam"}]
    """

    __tablename__ = "edu_evaluation_templates"

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    components: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    is_default: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
