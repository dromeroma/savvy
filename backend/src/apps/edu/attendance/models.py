"""SavvyEdu attendance model."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class EduAttendance(BaseMixin, OrgMixin, Base):
    """Attendance record per student per section per date."""

    __tablename__ = "edu_attendance"
    __table_args__ = (
        UniqueConstraint("section_id", "student_id", "date", name="uq_edu_attendance_section_student_date"),
    )

    section_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_sections.id", ondelete="CASCADE"), nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_students.id", ondelete="CASCADE"), nullable=False,
    )
    date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="present")  # present, absent, late, excused
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
