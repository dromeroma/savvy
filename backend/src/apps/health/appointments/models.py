"""SavvyHealth appointment model."""

import uuid
from datetime import date, datetime, time
from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Time, Uuid
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class HealthAppointment(BaseMixin, OrgMixin, Base):
    __tablename__ = "health_appointments"

    patient_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_patients.id", ondelete="CASCADE"), nullable=False)
    provider_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("health_providers.id", ondelete="CASCADE"), nullable=False)
    service_id: Mapped[uuid.UUID | None] = mapped_column(Uuid, ForeignKey("health_services.id", ondelete="SET NULL"), nullable=True)
    appointment_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[str] = mapped_column(String(5), nullable=False)  # "08:00"
    end_time: Mapped[str] = mapped_column(String(5), nullable=False)    # "08:30"
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False, default=30)
    reason: Mapped[str | None] = mapped_column(String(200), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="scheduled")
    # scheduled, confirmed, in_progress, completed, cancelled, no_show
    amount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    payment_status: Mapped[str] = mapped_column(String(20), nullable=False, default="pending")
    # pending, paid, insurance
