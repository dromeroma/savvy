"""SavvyEdu enrollment models — sections, enrollments, waitlists."""

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class EduSection(BaseMixin, OrgMixin, Base):
    """An instance of a course in a specific academic period (e.g., MAT101-A 2026-I)."""

    __tablename__ = "edu_sections"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", "academic_period_id", name="uq_edu_sections_org_code_period"),
    )

    course_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_courses.id", ondelete="CASCADE"), nullable=False,
    )
    academic_period_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_academic_periods.id", ondelete="CASCADE"), nullable=False,
    )
    teacher_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_teachers.id", ondelete="SET NULL"), nullable=True,
    )
    code: Mapped[str] = mapped_column(String(30), nullable=False)  # MAT101-A
    capacity: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    enrolled_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="open")  # open, closed, cancelled


class EduEnrollment(BaseMixin, OrgMixin, Base):
    """Student enrollment in a section."""

    __tablename__ = "edu_enrollments"
    __table_args__ = (
        UniqueConstraint("student_id", "section_id", name="uq_edu_enrollments_student_section"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_students.id", ondelete="CASCADE"), nullable=False,
    )
    section_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_sections.id", ondelete="CASCADE"), nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="enrolled",
    )  # enrolled, dropped, completed, failed, withdrawn
    enrolled_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="now()")


class EduWaitlist(BaseMixin, OrgMixin, Base):
    """Waitlist for a full section."""

    __tablename__ = "edu_waitlists"
    __table_args__ = (
        UniqueConstraint("student_id", "section_id", name="uq_edu_waitlists_student_section"),
    )

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_students.id", ondelete="CASCADE"), nullable=False,
    )
    section_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_sections.id", ondelete="CASCADE"), nullable=False,
    )
    position: Mapped[int] = mapped_column(Integer, nullable=False)
