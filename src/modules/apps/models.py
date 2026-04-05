"""App Registry, Organization Apps, and App User Roles SQLAlchemy 2.0 models."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, String, Text, UniqueConstraint, Uuid, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin


class AppRegistry(Base):
    """Catalog of available apps in the Savvy ecosystem.

    Does not use BaseMixin because the DB table lacks updated_at.
    """

    __tablename__ = "app_registry"

    id: Mapped[uuid.UUID] = mapped_column(
        Uuid, primary_key=True, default=uuid.uuid4,
    )
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    icon: Mapped[str | None] = mapped_column(String(100), nullable=True)
    color: Mapped[str | None] = mapped_column(String(7), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    requires: Mapped[dict] = mapped_column(JSONB, default=list)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )


class OrganizationApp(BaseMixin, Base):
    """Links an organization to an activated app."""

    __tablename__ = "organization_apps"
    __table_args__ = (
        UniqueConstraint("organization_id", "app_id", name="uq_organization_apps_org_app"),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False, index=True,
    )
    app_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False,
    )
    status: Mapped[str] = mapped_column(String(30), default="active", nullable=False)
    activated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False,
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    trial_ends_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True,
    )
    settings: Mapped[dict] = mapped_column(JSONB, default=dict)


class AppUserRole(BaseMixin, Base):
    """Per-app role assignment for a user within an organization."""

    __tablename__ = "app_user_roles"
    __table_args__ = (
        UniqueConstraint(
            "organization_id", "user_id", "app_id",
            name="uq_app_user_roles_org_user_app",
        ),
    )

    organization_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False, index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False,
    )
    app_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, nullable=False,
    )
    role: Mapped[str] = mapped_column(String(50), nullable=False)
