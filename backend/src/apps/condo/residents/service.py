"""Business logic for condo residents and visitors."""

from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.condo.residents.models import CondoResident, CondoVisitor
from src.apps.condo.residents.schemas import ResidentCreate, VisitorCreate


class ResidentService:
    @staticmethod
    async def list_residents(db: AsyncSession, org_id: uuid.UUID, unit_id: uuid.UUID | None = None) -> list[CondoResident]:
        q = select(CondoResident).where(CondoResident.organization_id == org_id)
        if unit_id: q = q.where(CondoResident.unit_id == unit_id)
        return list((await db.execute(q.order_by(CondoResident.created_at))).scalars().all())

    @staticmethod
    async def create_resident(db: AsyncSession, org_id: uuid.UUID, data: ResidentCreate) -> CondoResident:
        r = CondoResident(organization_id=org_id, **data.model_dump())
        db.add(r); await db.flush(); await db.refresh(r); return r

    @staticmethod
    async def list_visitors(db: AsyncSession, org_id: uuid.UUID, status_filter: str | None = None) -> list[CondoVisitor]:
        q = select(CondoVisitor).where(CondoVisitor.organization_id == org_id)
        if status_filter: q = q.where(CondoVisitor.status == status_filter)
        return list((await db.execute(q.order_by(CondoVisitor.entry_time.desc()))).scalars().all())

    @staticmethod
    async def register_visitor(db: AsyncSession, org_id: uuid.UUID, data: VisitorCreate) -> CondoVisitor:
        v = CondoVisitor(organization_id=org_id, **data.model_dump())
        db.add(v); await db.flush(); await db.refresh(v); return v

    @staticmethod
    async def exit_visitor(db: AsyncSession, org_id: uuid.UUID, visitor_id: uuid.UUID) -> CondoVisitor:
        result = await db.execute(select(CondoVisitor).where(CondoVisitor.id == visitor_id, CondoVisitor.organization_id == org_id))
        v = result.scalar_one_or_none()
        if v is None: raise NotFoundError("Visitor not found.")
        v.exit_time = datetime.now(UTC); v.status = "exited"
        await db.flush(); await db.refresh(v); return v
