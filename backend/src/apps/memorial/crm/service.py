"""Lógica de CRM (leads + comunicaciones)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.crm.schemas import (
    CommunicationCreate,
    LeadCreate,
    LeadUpdate,
)
from src.apps.memorial.models import (
    MemorialLead,
    MemorialLeadCommunication,
)
from src.core.exceptions import NotFoundError, ValidationError


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


async def _next_lead_consecutive(db: AsyncSession, org_id: uuid.UUID) -> int:
    last = await db.scalar(
        select(func.max(MemorialLead.consecutive)).where(MemorialLead.organization_id == org_id)
    )
    return (last or 0) + 1


def _format_lead_code(n: int) -> str:
    return f"LEAD-{n:04d}"


# ---------------------------------------------------------------- Leads


class LeadsService:

    @staticmethod
    async def list_(
        db: AsyncSession,
        org_id: uuid.UUID,
        *,
        status: str | None = None,
        source: str | None = None,
        assigned_to: uuid.UUID | None = None,
        search: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ):
        stmt = (
            select(MemorialLead)
            .where(MemorialLead.organization_id == org_id)
            .order_by(MemorialLead.created_at.desc())
            .limit(limit).offset(offset)
        )
        if status:
            stmt = stmt.where(MemorialLead.status == status)
        if source:
            stmt = stmt.where(MemorialLead.source == source)
        if assigned_to:
            stmt = stmt.where(MemorialLead.assigned_to == assigned_to)
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    MemorialLead.first_name.ilike(like),
                    MemorialLead.last_name.ilike(like),
                    MemorialLead.business_name.ilike(like),
                    MemorialLead.email.ilike(like),
                    MemorialLead.mobile.ilike(like),
                    MemorialLead.phone.ilike(like),
                    MemorialLead.document_number.ilike(like),
                    MemorialLead.code.ilike(like),
                )
            )
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, lid: uuid.UUID) -> MemorialLead:
        lead = await db.scalar(
            select(MemorialLead).where(
                MemorialLead.id == lid,
                MemorialLead.organization_id == org_id,
            )
        )
        if lead is None:
            raise NotFoundError("Lead no encontrado.")
        return lead

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: LeadCreate, created_by: uuid.UUID | None
    ) -> MemorialLead:
        if not any([data.first_name, data.last_name, data.business_name]):
            raise ValidationError("Debe indicar al menos un nombre (persona o empresa).")
        n = await _next_lead_consecutive(db, org_id)
        lead = MemorialLead(
            organization_id=org_id,
            consecutive=n,
            code=_format_lead_code(n),
            status="new",
            created_by=created_by,
            **data.model_dump(),
        )
        db.add(lead)
        await db.flush()
        await db.refresh(lead)
        return lead

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, lid: uuid.UUID, data: LeadUpdate
    ) -> MemorialLead:
        lead = await LeadsService.get(db, org_id, lid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(lead, k, v)
        await db.flush()
        await db.refresh(lead)
        return lead

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, lid: uuid.UUID) -> None:
        lead = await LeadsService.get(db, org_id, lid)
        await db.delete(lead)
        await db.flush()

    @staticmethod
    async def convert_to_contract(
        db: AsyncSession, org_id: uuid.UUID, lid: uuid.UUID, contract_id: uuid.UUID
    ) -> MemorialLead:
        lead = await LeadsService.get(db, org_id, lid)
        lead.converted_contract_id = contract_id
        lead.converted_at = _now_utc()
        lead.status = "won"
        await db.flush()
        await db.refresh(lead)
        return lead

    @staticmethod
    async def convert_to_service(
        db: AsyncSession, org_id: uuid.UUID, lid: uuid.UUID, service_id: uuid.UUID
    ) -> MemorialLead:
        lead = await LeadsService.get(db, org_id, lid)
        lead.converted_service_id = service_id
        lead.converted_at = _now_utc()
        lead.status = "won"
        await db.flush()
        await db.refresh(lead)
        return lead

    @staticmethod
    async def mark_lost(
        db: AsyncSession, org_id: uuid.UUID, lid: uuid.UUID, reason: str
    ) -> MemorialLead:
        lead = await LeadsService.get(db, org_id, lid)
        lead.status = "lost"
        lead.lost_reason = reason
        await db.flush()
        await db.refresh(lead)
        return lead


# ---------------------------------------------------------------- Communications


class CommunicationsService:

    @staticmethod
    async def list_for_lead(
        db: AsyncSession, org_id: uuid.UUID, lead_id: uuid.UUID
    ) -> list[MemorialLeadCommunication]:
        await LeadsService.get(db, org_id, lead_id)
        rows = await db.execute(
            select(MemorialLeadCommunication)
            .where(
                MemorialLeadCommunication.organization_id == org_id,
                MemorialLeadCommunication.lead_id == lead_id,
            )
            .order_by(MemorialLeadCommunication.occurred_at.desc())
        )
        return list(rows.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession,
        org_id: uuid.UUID,
        lead_id: uuid.UUID,
        data: CommunicationCreate,
        created_by: uuid.UUID | None,
    ) -> MemorialLeadCommunication:
        await LeadsService.get(db, org_id, lead_id)
        payload = data.model_dump()
        if payload.get("occurred_at") is None:
            payload["occurred_at"] = _now_utc()
        comm = MemorialLeadCommunication(
            organization_id=org_id,
            lead_id=lead_id,
            created_by=created_by,
            **payload,
        )
        db.add(comm)
        await db.flush()
        await db.refresh(comm)
        return comm

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, comm_id: uuid.UUID) -> None:
        comm = await db.scalar(
            select(MemorialLeadCommunication).where(
                MemorialLeadCommunication.id == comm_id,
                MemorialLeadCommunication.organization_id == org_id,
            )
        )
        if comm is None:
            raise NotFoundError("Comunicación no encontrada.")
        await db.delete(comm)
        await db.flush()
