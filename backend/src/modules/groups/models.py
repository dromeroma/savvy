"""SQLAlchemy 2.0 models for organizational scopes, groups, and memberships."""

import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class OrganizationalScope(BaseMixin, OrgMixin, Base):
    """Hierarchical organizational unit (country, zone, district, church)."""

    __tablename__ = "organizational_scopes"
    __table_args__ = (
        UniqueConstraint("organization_id", "type", "code", name="uq_org_scopes_org_type_code"),
    )

    type: Mapped[str] = mapped_column(String(30), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    leader_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Relationships
    parent: Mapped["OrganizationalScope | None"] = relationship(
        remote_side="OrganizationalScope.id", lazy="selectin",
    )
    leaders: Mapped[list["ScopeLeader"]] = relationship(
        back_populates="scope", cascade="all, delete-orphan",
    )


class ScopeLeader(Base):
    """Leadership assignment within an organizational scope."""

    __tablename__ = "scope_leaders"
    __table_args__ = (
        UniqueConstraint("scope_id", "person_id", "role", name="uq_scope_leaders_scope_person_role"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    scope_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
    started_at: Mapped[date] = mapped_column(Date, nullable=False)
    ended_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )

    # Relationships
    scope: Mapped["OrganizationalScope"] = relationship(back_populates="leaders")


class GroupType(BaseMixin, Base):
    """Configurable group classification (ministry, cell, committee, etc.)."""

    __tablename__ = "group_types"
    __table_args__ = (
        UniqueConstraint("organization_id", "code", name="uq_group_types_org_code"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    app_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    code: Mapped[str] = mapped_column(String(50), nullable=False)
    allow_hierarchy: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    requires_classes: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    requires_attendance: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    requires_activities: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    max_members: Mapped[int | None] = mapped_column(Integer, nullable=True)
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")


class Group(BaseMixin, OrgMixin, Base):
    """A concrete group instance within the organization."""

    __tablename__ = "groups"

    group_type_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("group_types.id", ondelete="RESTRICT"), nullable=False,
    )
    scope_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("organizational_scopes.id", ondelete="SET NULL"), nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("groups.id", ondelete="SET NULL"), nullable=True,
    )
    leader_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="SET NULL"), nullable=True,
    )
    status: Mapped[str] = mapped_column(String(20), default="active", server_default="active")
    settings: Mapped[dict] = mapped_column(JSONB, default=dict, server_default="{}")

    # Relationships
    group_type: Mapped["GroupType"] = relationship(lazy="selectin")
    scope: Mapped["OrganizationalScope | None"] = relationship(lazy="selectin")
    parent: Mapped["Group | None"] = relationship(
        remote_side="Group.id", lazy="selectin",
    )
    members: Mapped[list["GroupMember"]] = relationship(
        back_populates="group", cascade="all, delete-orphan",
    )


class GroupMember(Base):
    """Person membership within a group."""

    __tablename__ = "group_members"
    __table_args__ = (
        UniqueConstraint("group_id", "person_id", name="uq_group_members_group_person"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("organizations.id", ondelete="CASCADE"), index=True, nullable=False,
    )
    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("groups.id", ondelete="CASCADE"), nullable=False,
    )
    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), default="member", server_default="member")
    joined_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    left_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )

    # Relationships
    group: Mapped["Group"] = relationship(back_populates="members")
