"""SavvyEdu grading models — evaluations, grades, final grades."""

import uuid
from datetime import date, datetime

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class EduEvaluation(BaseMixin, OrgMixin, Base):
    """An evaluative activity within a section (exam, quiz, assignment, etc.)."""

    __tablename__ = "edu_evaluations"

    section_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_sections.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="exam")  # exam, quiz, assignment, project, participation
    weight: Mapped[float] = mapped_column(Numeric(4, 3), nullable=False, default=0)  # 0.000 to 1.000
    max_score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False, default=100)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active, cancelled


class EduGrade(BaseMixin, OrgMixin, Base):
    """Individual grade for a student on an evaluation."""

    __tablename__ = "edu_grades"
    __table_args__ = (
        UniqueConstraint("evaluation_id", "student_id", name="uq_edu_grades_eval_student"),
    )

    evaluation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_evaluations.id", ondelete="CASCADE"), nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_students.id", ondelete="CASCADE"), nullable=False,
    )
    score: Mapped[float] = mapped_column(Numeric(7, 2), nullable=False)
    percentage: Mapped[float | None] = mapped_column(Numeric(5, 2), nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)
    graded_by: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    graded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class EduFinalGrade(BaseMixin, OrgMixin, Base):
    """Consolidated final grade for a student in a section/period."""

    __tablename__ = "edu_final_grades"
    __table_args__ = (
        UniqueConstraint("student_id", "section_id", name="uq_edu_final_grades_student_section"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_students.id", ondelete="CASCADE"), nullable=False,
    )
    section_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_sections.id", ondelete="CASCADE"), nullable=False,
    )
    academic_period_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_academic_periods.id", ondelete="CASCADE"), nullable=False,
    )
    numeric_grade: Mapped[float] = mapped_column(Numeric(5, 2), nullable=False)
    letter_grade: Mapped[str | None] = mapped_column(String(10), nullable=True)
    gpa_points: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, approved, failed
