"""Business logic for CRM leads."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.crm.leads.models import CrmLead
from src.apps.crm.leads.schemas import LeadCreate, LeadUpdate


class LeadService:

    @staticmethod
    async def list_leads(db: AsyncSession, org_id: uuid.UUID, status_filter: str | None = None) -> list[CrmLead]:
        q = select(CrmLead).where(CrmLead.organization_id == org_id)
        if status_filter:
            q = q.where(CrmLead.status == status_filter)
        return list((await db.execute(q.order_by(CrmLead.created_at.desc()))).scalars().all())

    @staticmethod
    async def create_lead(db: AsyncSession, org_id: uuid.UUID, data: LeadCreate) -> CrmLead:
        lead = CrmLead(organization_id=org_id, contact_id=data.contact_id, source=data.source, score=data.score, notes=data.notes)
        db.add(lead)
        await db.flush()
        await db.refresh(lead)
        return lead

    @staticmethod
    async def get_lead(db: AsyncSession, org_id: uuid.UUID, lead_id: uuid.UUID) -> CrmLead:
        result = await db.execute(select(CrmLead).where(CrmLead.id == lead_id, CrmLead.organization_id == org_id))
        lead = result.scalar_one_or_none()
        if lead is None:
            raise NotFoundError("Lead not found.")
        return lead

    @staticmethod
    async def update_lead(db: AsyncSession, org_id: uuid.UUID, lead_id: uuid.UUID, data: LeadUpdate) -> CrmLead:
        lead = await LeadService.get_lead(db, org_id, lead_id)
        for f, v in data.model_dump(exclude_unset=True).items():
            setattr(lead, f, v)
        await db.flush()
        await db.refresh(lead)
        return lead
