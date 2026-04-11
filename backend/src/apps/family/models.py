"""SavvyFamily models — family units, enhanced relationships, and clinical annotations.

Builds on top of the shared `people` and `family_relationships` tables.
Adds family grouping, relationship metadata, and genogram markers.
"""

import uuid
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class FamilyUnit(BaseMixin, OrgMixin, Base):
    """A household / family unit that groups people together."""

    __tablename__ = "family_units"

    name: Mapped[str] = mapped_column(String(200), nullable=False)  # "Familia Rodríguez López"
    type: Mapped[str] = mapped_column(String(30), nullable=False, default="nuclear")
    # nuclear, extended, single_parent, blended, other
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class FamilyMember(BaseMixin, OrgMixin, Base):
    """Links a person to a family unit with a role."""

    __tablename__ = "family_members"
    __table_args__ = (
        UniqueConstraint("family_unit_id", "person_id", name="uq_family_members_unit_person"),
    )

    family_unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("family_units.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    role: Mapped[str] = mapped_column(String(30), nullable=False, default="member")
    # head, spouse, child, grandchild, grandparent, uncle_aunt, cousin, in_law, other
    is_deceased: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    death_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    generation: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    # 0 = reference generation, -1 = parents, -2 = grandparents, 1 = children, 2 = grandchildren
    position_x: Mapped[int | None] = mapped_column(Integer, nullable=True)  # for genogram layout persistence
    position_y: Mapped[int | None] = mapped_column(Integer, nullable=True)


class FamilyRelationshipMeta(BaseMixin, Base):
    """Extended metadata for a family relationship (marriages, divorces, etc.).

    Links to the existing family_relationships table via the two person_ids.
    """

    __tablename__ = "family_relationship_meta"
    __table_args__ = (
        UniqueConstraint("family_unit_id", "person_id", "related_to_id", name="uq_family_rel_meta_unit_persons"),
    )

    family_unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("family_units.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    related_to_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    relationship_type: Mapped[str] = mapped_column(String(30), nullable=False)
    # married, divorced, separated, engaged, cohabiting, widowed
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")
    # active, ended, deceased
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)


class FamilyAnnotation(BaseMixin, OrgMixin, Base):
    """Clinical/pastoral annotation on a person within a family context.

    Standard genogram markers: substance_abuse, mental_health, physical_illness,
    violence, sexual_abuse, emotional_abuse, conflict, cutoff, etc.
    """

    __tablename__ = "family_annotations"

    family_unit_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("family_units.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    # If person_id is null, annotation applies to the family unit itself
    category: Mapped[str] = mapped_column(String(50), nullable=False)
    # substance_abuse, mental_health, physical_illness, violence, sexual_abuse,
    # emotional_abuse, conflict, cutoff, enmeshment, estrangement,
    # disability, incarceration, adoption, miscarriage, abortion, stillbirth,
    # spiritual (for church), financial, other
    severity: Mapped[str] = mapped_column(String(20), nullable=False, default="moderate")
    # mild, moderate, severe
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    diagnosed_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    resolved_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    source_app: Mapped[str | None] = mapped_column(String(20), nullable=True)  # church, health, edu
