"""SavvyEdu finance models — tuition plans, student charges, scholarships."""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, Numeric, String, Text, UniqueConstraint, Uuid, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class EduTuitionPlan(BaseMixin, OrgMixin, Base):
    """Tuition plan for a program in a given period."""

    __tablename__ = "edu_tuition_plans"

    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_programs.id", ondelete="CASCADE"), nullable=False,
    )
    academic_period_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_academic_periods.id", ondelete="CASCADE"), nullable=False,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    total_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    installments: Mapped[dict] = mapped_column(JSONB, nullable=False, default=list)
    # [{due_date: "2026-03-01", amount: 500000}, ...]


class EduStudentCharge(BaseMixin, OrgMixin, Base):
    """Individual charge to a student from a tuition plan."""

    __tablename__ = "edu_student_charges"

    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_students.id", ondelete="CASCADE"), nullable=False,
    )
    tuition_plan_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_tuition_plans.id", ondelete="SET NULL"), nullable=True,
    )
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")  # pending, paid, overdue, cancelled
    finance_transaction_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)


class EduScholarship(BaseMixin, OrgMixin, Base):
    """Scholarship or discount definition."""

    __tablename__ = "edu_scholarships"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="percentage")  # percentage, fixed
    value: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    criteria: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    academic_period_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_academic_periods.id", ondelete="SET NULL"), nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class EduScholarshipAward(BaseMixin, OrgMixin, Base):
    """Scholarship awarded to a specific student."""

    __tablename__ = "edu_scholarship_awards"

    scholarship_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_scholarships.id", ondelete="CASCADE"), nullable=False,
    )
    student_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("edu_students.id", ondelete="CASCADE"), nullable=False,
    )
    applied_amount: Mapped[float] = mapped_column(Numeric(15, 2), nullable=False)
    academic_period_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("edu_academic_periods.id", ondelete="SET NULL"), nullable=True,
    )
