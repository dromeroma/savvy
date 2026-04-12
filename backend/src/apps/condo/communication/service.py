"""Business logic for condo announcements."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.apps.condo.communication.models import CondoAnnouncement
from src.apps.condo.communication.schemas import AnnouncementCreate


class CommunicationService:
    @staticmethod
    async def list_announcements(db: AsyncSession, org_id: uuid.UUID) -> list[CondoAnnouncement]:
        return list((await db.execute(select(CondoAnnouncement).where(CondoAnnouncement.organization_id == org_id).order_by(CondoAnnouncement.created_at.desc()))).scalars().all())

    @staticmethod
    async def create_announcement(db: AsyncSession, org_id: uuid.UUID, data: AnnouncementCreate) -> CondoAnnouncement:
        a = CondoAnnouncement(organization_id=org_id, **data.model_dump())
        db.add(a); await db.flush(); await db.refresh(a); return a
