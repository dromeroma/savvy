"""Subscribers REST endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.subscribers.schemas import (
    ServiceActionRequest,
    SubscriberCreate,
    SubscriberListItem,
    SubscriberResponse,
    SubscriberUpdate,
)
from src.apps.water.subscribers.service import SubscribersService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(
    prefix="/subscribers",
    tags=["Water · Suscriptores"],
)


@router.get(
    "",
    response_model=list[SubscriberListItem],
    dependencies=[Depends(require_permission("water", "subscribers.read", "subscribers.manage"))],
)
async def list_subscribers(
    search: str | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    subscriber_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SubscribersService.list_subscribers(
        db, org_id, search=search, status=status_,
        subscriber_type=subscriber_type, limit=limit, offset=offset,
    )


@router.get(
    "/{subscriber_id}",
    response_model=SubscriberResponse,
    dependencies=[Depends(require_permission("water", "subscribers.read", "subscribers.manage"))],
)
async def get_subscriber(
    subscriber_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SubscribersService.get_subscriber(db, org_id, subscriber_id)


@router.post(
    "",
    response_model=SubscriberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "subscribers.manage"))],
)
async def create_subscriber(
    data: SubscriberCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SubscribersService.create_subscriber(db, org_id, data)


@router.patch(
    "/{subscriber_id}",
    response_model=SubscriberResponse,
    dependencies=[Depends(require_permission("water", "subscribers.manage"))],
)
async def update_subscriber(
    subscriber_id: uuid.UUID,
    data: SubscriberUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SubscribersService.update_subscriber(db, org_id, subscriber_id, data)


@router.delete(
    "/{subscriber_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("water", "subscribers.manage"))],
)
async def delete_subscriber(
    subscriber_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await SubscribersService.delete_subscriber(db, org_id, subscriber_id)


@router.post(
    "/{subscriber_id}/suspend",
    response_model=SubscriberResponse,
    dependencies=[Depends(require_permission("water", "subscribers.manage", "service.manage"))],
)
async def suspend_subscriber(
    subscriber_id: uuid.UUID,
    data: ServiceActionRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SubscribersService.suspend(
        db, org_id, subscriber_id,
        reason=data.reason, create_fee_invoice=data.create_fee_invoice,
    )


@router.post(
    "/{subscriber_id}/reconnect",
    response_model=SubscriberResponse,
    dependencies=[Depends(require_permission("water", "subscribers.manage", "service.manage"))],
)
async def reconnect_subscriber(
    subscriber_id: uuid.UUID,
    data: ServiceActionRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await SubscribersService.reconnect(
        db, org_id, subscriber_id,
        reason=data.reason, create_fee_invoice=data.create_fee_invoice,
    )
