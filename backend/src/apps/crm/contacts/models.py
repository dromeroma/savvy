"""SavvyCRM contact and company models."""

import uuid

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text, UniqueConstraint, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.core.database import Base
from src.core.models.base import BaseMixin, OrgMixin


class CrmContact(BaseMixin, OrgMixin, Base):
    """CRM-specific data for a person. Extends people table."""

    __tablename__ = "crm_contacts"
    __table_args__ = (
        UniqueConstraint("organization_id", "person_id", name="uq_crm_contacts_org_person"),
    )

    person_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("people.id", ondelete="CASCADE"), nullable=False,
    )
    source: Mapped[str | None] = mapped_column(String(50), nullable=True)
    # website, referral, social_media, cold_call, event, advertising, other
    lifecycle_stage: Mapped[str] = mapped_column(String(30), nullable=False, default="subscriber")
    # subscriber, lead, qualified_lead, opportunity, customer, evangelist
    lead_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    assigned_to: Mapped[uuid.UUID | None] = mapped_column(Uuid, nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    last_contacted: Mapped[str | None] = mapped_column(String(30), nullable=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class CrmCompany(BaseMixin, OrgMixin, Base):
    """A company/organization in the CRM."""

    __tablename__ = "crm_companies"
    __table_args__ = (
        UniqueConstraint("organization_id", "name", name="uq_crm_companies_org_name"),
    )

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    industry: Mapped[str | None] = mapped_column(String(100), nullable=True)
    website: Mapped[str | None] = mapped_column(String(300), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    country: Mapped[str | None] = mapped_column(String(10), nullable=True)
    size: Mapped[str | None] = mapped_column(String(30), nullable=True)
    # startup, small, medium, large, enterprise
    annual_revenue: Mapped[float | None] = mapped_column(Numeric(15, 2), nullable=True)
    tags: Mapped[list] = mapped_column(JSONB, nullable=False, default=list)
    custom_fields: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="active")


class CrmContactCompany(BaseMixin, Base):
    """Links a contact to a company with a role."""

    __tablename__ = "crm_contact_companies"
    __table_args__ = (
        UniqueConstraint("contact_id", "company_id", name="uq_crm_contact_company"),
    )

    contact_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("crm_contacts.id", ondelete="CASCADE"), nullable=False,
    )
    company_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("crm_companies.id", ondelete="CASCADE"), nullable=False,
    )
    role: Mapped[str | None] = mapped_column(String(100), nullable=True)
    is_primary: Mapped[bool] = mapped_column(default=False, nullable=False)
