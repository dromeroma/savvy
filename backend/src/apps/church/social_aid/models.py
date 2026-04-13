"""Social aid models: programs, beneficiaries, distributions."""

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import Date, ForeignKey, Integer, Numeric, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class ChurchAidProgram(BaseMixin, OrgMixin, Base):
    """A social aid program (food, clothing, medical, etc.)."""

    __tablename__ = "church_aid_programs"

    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    program_type: Mapped[str] = mapped_column(String(40), default="food", nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    budget_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)


class ChurchAidBeneficiary(BaseMixin, OrgMixin, Base):
    """Beneficiary of an aid program — may be an existing Person or external."""

    __tablename__ = "church_aid_beneficiaries"

    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_aid_programs.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    external_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    external_document: Mapped[str | None] = mapped_column(String(50), nullable=True)
    external_phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    need_category: Mapped[str | None] = mapped_column(String(60), nullable=True)
    household_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)


class ChurchAidDistribution(BaseMixin, OrgMixin, Base):
    """One aid delivery to a beneficiary."""

    __tablename__ = "church_aid_distributions"

    program_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_aid_programs.id", ondelete="CASCADE"), nullable=False,
    )
    beneficiary_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("church_aid_beneficiaries.id", ondelete="CASCADE"), nullable=False,
    )
    distribution_date: Mapped[date] = mapped_column(Date, nullable=False)
    item_description: Mapped[str] = mapped_column(String(300), nullable=False)
    quantity: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)
    estimated_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)
    delivered_by: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
