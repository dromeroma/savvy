"""SavvyHealth provider (doctor) model."""

import uuid
from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class HealthProvider(BaseMixin, OrgMixin, Base):
    """A healthcare provider (doctor, specialist, therapist)."""
    __tablename__ = "health_providers"
    __table_args__ = (UniqueConstraint("organization_id", "person_id", name="uq_health_providers_org_person"),)

    person_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False)
    provider_code: Mapped[str | None] = mapped_column(String(30), nullable=True)
    specialty: Mapped[str] = mapped_column(String(100), nullable=False)
    license_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    consultation_duration: Mapped[int] = mapped_column(default=30, nullable=False)  # minutes
    schedule: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    # {"mon": [{"from": "08:00", "to": "12:00"}, {"from": "14:00", "to": "18:00"}]}
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
