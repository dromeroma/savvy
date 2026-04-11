"""SavvyEdu academic structure models — periods, programs, courses,
prerequisites, and curriculum versions.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class EduAcademicPeriod(BaseMixin, OrgMixin, Base):
    """A concrete academic period instance (e.g., 2026-I, 2026-II)."""

    __tablename__ = "edu_academic_periods"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_edu_periods_org_name"),
    )

    period_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_academic_period_types.id", ondelete="RESTRICT"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)  # "2026-I"
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="planned")  # planned, active, closed


class EduProgram(BaseMixin, OrgMixin, Base):
    """An academic program (e.g., Computer Science, Nursing)."""

    __tablename__ = "edu_programs"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_edu_programs_org_code"),
    )

    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    grading_system_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_grading_systems.id", ondelete="SET NULL"), nullable=True,
    )
    evaluation_template_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_evaluation_templates.id", ondelete="SET NULL"), nullable=True,
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    degree_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # bachelor, master, technical, diploma
    duration_periods: Mapped[int | None] = mapped_column(Integer, nullable=True)  # number of periods to complete
    credits_required: Mapped[int | None] = mapped_column(Integer, nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active, inactive


class EduCourse(BaseMixin, OrgMixin, Base):
    """A course / subject (e.g., Calculus I, Data Structures)."""

    __tablename__ = "edu_courses"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_edu_courses_org_code"),
    )

    program_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_programs.id", ondelete="SET NULL"), nullable=True,
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    weekly_hours: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_elective: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")

    prerequisites: Mapped[list["EduPrerequisite"]] = relationship(
        foreign_keys="EduPrerequisite.course_id",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class EduPrerequisite(BaseMixin, Base):
    """Prerequisite relationship between courses."""

    __tablename__ = "edu_prerequisites"
    __table_args__ = (
        UniqueConstraint("course_id", "prerequisite_id", name="uq_edu_prereq_course_prereq"),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_courses.id", ondelete="CASCADE"), nullable=False,
    )
    prerequisite_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_courses.id", ondelete="CASCADE"), nullable=False,
    )
    min_grade: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)


class EduCurriculumVersion(BaseMixin, Base):
    """A versioned curriculum map for a program.

    course_map is JSONB:
    {"1": ["COURSE_CODE_1", "COURSE_CODE_2"], "2": ["COURSE_CODE_3"], ...}
    where keys are period numbers and values are course codes.
    """

    __tablename__ = "edu_curriculum_versions"

    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_programs.id", ondelete="CASCADE"), nullable=False,
    )
    version: Mapped[str] = mapped_column(String(20), nullable=False)  # "v1", "2026"
    effective_from: Mapped[date] = mapped_column(Date, nullable=False)
    course_map: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
