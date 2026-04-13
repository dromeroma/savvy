"""Church events REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.church.events.schemas import EventCreate, EventResponse, EventUpdate
from src.apps.church.events.service import EventService

router = APIRouter(prefix="/events", tags=["Church Events"])

_READ = [Depends(require_permission("church", "events.manage", "members.read", "reports.view"))]
_WRITE = [Depends(require_permission("church", "events.manage"))]


@router.get("/", response_model=list[EventResponse], dependencies=_READ)
async def list_events(
    type: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EventService.list_events(db, org_id, type_=type, status=status_filter)


@router.post("/", response_model=EventResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_event(
    data: EventCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EventService.create_event(db, org_id, data)


@router.get("/{event_id}", response_model=EventResponse, dependencies=_READ)
async def get_event(
    event_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EventService.get_event(db, org_id, event_id)


@router.patch("/{event_id}", response_model=EventResponse, dependencies=_WRITE)
async def update_event(
    event_id: uuid.UUID,
    data: EventUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EventService.update_event(db, org_id, event_id, data)
