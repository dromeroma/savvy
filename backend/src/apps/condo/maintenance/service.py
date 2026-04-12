"""Business logic for condo maintenance."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.condo.maintenance.models import CondoMaintenance
from src.apps.condo.maintenance.schemas import MaintenanceCreate, MaintenanceUpdate


class MaintenanceService:
    @staticmethod
    async def list_requests(db: AsyncSession, org_id: uuid.UUID, status_filter: str | None = None) -> list[CondoMaintenance]:
        q = select(CondoMaintenance).where(CondoMaintenance.organization_id == org_id)
        if status_filter: q = q.where(CondoMaintenance.status == status_filter)
        return list((await db.execute(q.order_by(CondoMaintenance.created_at.desc()))).scalars().all())

    @staticmethod
    async def create_request(db: AsyncSession, org_id: uuid.UUID, data: MaintenanceCreate) -> CondoMaintenance:
        m = CondoMaintenance(organization_id=org_id, **data.model_dump())
        db.add(m); await db.flush(); await db.refresh(m); return m

    @staticmethod
    async def update_request(db: AsyncSession, org_id: uuid.UUID, req_id: uuid.UUID, data: MaintenanceUpdate) -> CondoMaintenance:
        result = await db.execute(select(CondoMaintenance).where(CondoMaintenance.id == req_id, CondoMaintenance.organization_id == org_id))
        m = result.scalar_one_or_none()
        if m is None: raise NotFoundError("Request not found.")
        for f, v in data.model_dump(exclude_unset=True).items(): setattr(m, f, v)
        await db.flush(); await db.refresh(m); return m
