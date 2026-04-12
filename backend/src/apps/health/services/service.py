"""Business logic for health services."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.health.services.models import HealthService
from src.apps.health.services.schemas import ServiceCreate


class HealthServiceCatalog:
    @staticmethod
    async def list_services(db: AsyncSession, org_id: uuid.UUID) -> list[HealthService]:
        return list((await db.execute(select(HealthService).where(HealthService.organization_id == org_id).order_by(HealthService.name))).scalars().all())

    @staticmethod
    async def create_service(db: AsyncSession, org_id: uuid.UUID, data: ServiceCreate) -> HealthService:
        s = HealthService(organization_id=org_id, **data.model_dump())
        db.add(s); await db.flush(); await db.refresh(s); return s
