"""SavvyEdu teacher model — employment/academic data only.

Person data lives in the shared `people` table.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class EduTeacher(BaseMixin, OrgMixin, Base):
    """Employment and academic data for a teacher."""

    __tablename__ = "edu_teachers"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "person_id",
            name="uq_edu_teachers_org_person",
        ),
        UniqueConstraint(
            "organization_id", "employee_code",
            name="uq_edu_teachers_org_code",
        ),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    employee_code: Mapped[str] = mapped_column(String(30), nullable=False)
    department_scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    specialization: Mapped[str | None] = mapped_column(String(200), nullable=True)
    hire_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    contract_type: Mapped[str | None] = mapped_column(String(30), nullable=True)  # full_time, part_time, adjunct
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")  # active, inactive, on_leave
