"""SavvyHealth patient and insurance models."""

import uuid
from datetime import date
from sqlalchemy import Date, ForeignKey, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class HealthPatient(BaseMixin, OrgMixin, Base):
    """Patient record extending People with medical data."""
    __tablename__ = "health_patients"
    __table_args__ = (UniqueConstraint("organization_id", "person_id", name="uq_health_patients_org_person"),)

    person_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    patient_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    blood_type: Mapped[str | None] = mapped_column(String(5), nullable=True)  # A+, B-, O+, AB+
    allergies: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    chronic_conditions: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    current_medications: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    emergency_contact_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    emergency_contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class HealthInsurance(BaseMixin, OrgMixin, Base):
    """Patient insurance / EPS information."""
    __tablename__ = "health_insurance"

    patient_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_patients.id", ondelete="CASCADE"), nullable=False)
    provider_name: Mapped[str] = mapped_column(String(200), nullable=False)  # EPS name
    policy_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    plan_type: Mapped[str | None] = mapped_column(String(50), nullable=True)  # contributivo, subsidiado, prepagada
    coverage_details: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    valid_from: Mapped[date | None] = mapped_column(Date, nullable=True)
    valid_until: Mapped[date | None] = mapped_column(Date, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
