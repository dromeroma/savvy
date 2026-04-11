"""SavvyEdu student models — academic data only.

Person data (name, email, phone, etc.) lives in the shared `people` table.
This table stores education-specific attributes.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class EduStudent(BaseMixin, OrgMixin, Base):
    """Academic data for a person enrolled as a student."""

    __tablename__ = "edu_students"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "person_id",
            name="uq_edu_students_org_person",
        ),
        UniqueConstraint(
            "organization_id", "student_code",
            name="uq_edu_students_org_code",
        ),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    student_code: Mapped[str] = mapped_column(String(30), nullable=False)
    program_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_programs.id", ondelete="SET NULL"), nullable=True,
    )
    curriculum_version_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_curriculum_versions.id", ondelete="SET NULL"), nullable=True,
    )
    current_period_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_academic_periods.id", ondelete="SET NULL"), nullable=True,
    )
    admission_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    academic_status: Mapped[str] = mapped_column(
        String(30), nullable=False, default="active",
    )  # active, inactive, graduated, suspended, expelled
    cumulative_gpa: Mapped[float | None] = mapped_column(Numeric(4, 2), nullable=True)
    completed_credits: Mapped[int] = mapped_column(Integer, nullable=False, default=0)


class EduGuardian(BaseMixin, OrgMixin, Base):
    """Relationship between a guardian (parent/tutor) and a student."""

    __tablename__ = "edu_guardians"
    __table_args__ = (
        UniqueConstraint(
            "person_id", "student_id",
            name="uq_edu_guardians_person_student",
        ),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_students.id", ondelete="CASCADE"), nullable=False,
    )
    relationship: Mapped[str] = mapped_column(String(30), nullable=False)  # parent, mother, father, guardian, tutor
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
