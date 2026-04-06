"""Business logic for church events."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.events.models import ChurchEvent
from src.apps.church.events.schemas import EventCreate, EventUpdate
from src.core.exceptions import NotFoundError


class EventService:

    @staticmethod
    async def list_events(
        db: AsyncSession, org_id: uuid.UUID,
        type_: str | None = None, status: str | None = None,
    ) -> list[ChurchEvent]:
        stmt = (
            select(ChurchEvent)
            .where(ChurchEvent.organization_id == org_id)
            .order_by(ChurchEvent.date.desc())
        )
        if type_:
            stmt = stmt.where(ChurchEvent.type == type_)
        if status:
            stmt = stmt.where(ChurchEvent.status == status)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_event(
        db: AsyncSession, org_id: uuid.UUID, data: EventCreate,
    ) -> ChurchEvent:
        event = ChurchEvent(organization_id=org_id, **data.model_dump())
        db.add(event)
        await db.flush()
        await db.refresh(event)
        return event

    @staticmethod
    async def update_event(
        db: AsyncSession, org_id: uuid.UUID, event_id: uuid.UUID, data: EventUpdate,
    ) -> ChurchEvent:
        result = await db.execute(
            select(ChurchEvent).where(
                ChurchEvent.id == event_id,
                ChurchEvent.organization_id == org_id,
            )
        )
        event = result.scalar_one_or_none()
        if event is None:
            raise NotFoundError("Event not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(event, field, value)
        await db.flush()
        await db.refresh(event)
        return event

    @staticmethod
    async def get_event(
        db: AsyncSession, org_id: uuid.UUID, event_id: uuid.UUID,
    ) -> ChurchEvent:
        result = await db.execute(
            select(ChurchEvent).where(
                ChurchEvent.id == event_id,
                ChurchEvent.organization_id == org_id,
            )
        )
        event = result.scalar_one_or_none()
        if event is None:
            raise NotFoundError("Event not found.")
        return event
