"""SavvyHealth clinical records — EHR, vitals, diagnoses, prescriptions, lab orders, treatment plans, documents."""

import uuid
from datetime import date
from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class HealthClinicalRecord(BaseMixin, OrgMixin, Base):
    """A clinical encounter / consultation record."""
    __tablename__ = "health_clinical_records"

    patient_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_patients.id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_providers.id", ondelete="SET NULL"), nullable=True)
    appointment_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("health_appointments.id", ondelete="SET NULL"), nullable=True)
    record_date: Mapped[date] = mapped_column(Date, nullable=False)
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    present_illness: Mapped[str | None] = mapped_column(Text, nullable=True)
    physical_exam: Mapped[str | None] = mapped_column(Text, nullable=True)
    assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # Flexible structured data: templates, custom fields
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="draft")
    # draft, signed, amended


class HealthVitals(BaseMixin, OrgMixin, Base):
    """Vital signs recorded during a consultation."""
    __tablename__ = "health_vitals"

    record_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_clinical_records.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_patients.id", ondelete="CASCADE"), nullable=False)
    systolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    diastolic_bp: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heart_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    temperature: Mapped[float | None] = mapped_column(Numeric(4, 1), nullable=True)
    respiratory_rate: Mapped[int | None] = mapped_column(Integer, nullable=True)
    oxygen_saturation: Mapped[int | None] = mapped_column(Integer, nullable=True)
    weight_kg: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)
    height_cm: Mapped[float | None] = mapped_column(Numeric(5, 1), nullable=True)


class HealthDiagnosis(BaseMixin, OrgMixin, Base):
    __tablename__ = "health_diagnoses"

    record_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_clinical_records.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_patients.id", ondelete="CASCADE"), nullable=False)
    code: Mapped[str | None] = mapped_column(String(20), nullable=True)  # ICD-10
    name: Mapped[str] = mapped_column(String(300), nullable=False)
    diagnosis_type: Mapped[str] = mapped_column(String(20), nullable=False, default="primary")
    # primary, secondary, differential
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class HealthPrescription(BaseMixin, OrgMixin, Base):
    __tablename__ = "health_prescriptions"

    record_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_clinical_records.id", ondelete="CASCADE"), nullable=False)
    patient_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_patients.id", ondelete="CASCADE"), nullable=False)
    medication: Mapped[str] = mapped_column(String(200), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100), nullable=False)
    frequency: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[str | None] = mapped_column(String(50), nullable=True)
    instructions: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class HealthLabOrder(BaseMixin, OrgMixin, Base):
    __tablename__ = "health_lab_orders"

    record_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("health_clinical_records.id", ondelete="SET NULL"), nullable=True)
    patient_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_patients.id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("health_providers.id", ondelete="SET NULL"), nullable=True)
    test_name: Mapped[str] = mapped_column(String(200), nullable=False)
    test_code: Mapped[str | None] = mapped_column(String(20), nullable=True)
    urgency: Mapped[str] = mapped_column(String(20), nullable=False, default="routine")
    # routine, urgent, stat
    results: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    result_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="ordered")
    # ordered, collected, processing, completed, cancelled
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class HealthTreatmentPlan(BaseMixin, OrgMixin, Base):
    __tablename__ = "health_treatment_plans"

    patient_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_patients.id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("health_providers.id", ondelete="SET NULL"), nullable=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    goals: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # active, completed, discontinued


class HealthDocument(BaseMixin, OrgMixin, Base):
    """Medical documents: certificates, referrals, disability notes."""
    __tablename__ = "health_documents"

    patient_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_patients.id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("health_providers.id", ondelete="SET NULL"), nullable=True)
    doc_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # certificate, referral, disability, lab_result, prescription_print, other
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str | None] = mapped_column(Text, nullable=True)
    data: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
