"""Church congregant SQLAlchemy model — ecclesiastical data only.

Person data (name, email, phone, etc.) lives in the shared `people` table
via SavvyPeople.  This table stores church-specific attributes and links
to the person record via `person_id`.
"""

import uuid
from datetime import date

from sqlalchemy import Date, ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ChurchCongregant(BaseMixin, OrgMixin, Base):
    """Ecclesiastical data for a person registered in a church."""

    __tablename__ = "church_congregants"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "person_id",
            name="uq_church_congregants_org_person",
        ),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    membership_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    baptism_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    conversion_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    spiritual_status: Mapped[str | None] = mapped_column(String(30), nullable=True)
    referred_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    pastoral_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
