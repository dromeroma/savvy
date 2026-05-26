"""Endpoints REST de traslados."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.transfers.schemas import (
    TransferCreate,
    TransferListItem,
    TransferResponse,
    TransferTransitionRequest,
    TransferUpdate,
)
from src.apps.memorial.transfers.service import TransfersService
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/transfers", tags=["Memorial · Traslados"])


def _user_uuid(user: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(user["sub"])


@router.get(
    "",
    response_model=list[TransferListItem],
    dependencies=[Depends(require_permission(
        "memorial", "transfers.read", "transfers.manage",
        "services.read", "services.manage",
    ))],
)
async def list_transfers(
    service_id: uuid.UUID | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TransfersService.list_transfers(
        db, org_id,
        service_id=service_id, status=status_,
        date_from=date_from, date_to=date_to,
        limit=limit, offset=offset,
    )


@router.get(
    "/{tid}",
    response_model=TransferResponse,
    dependencies=[Depends(require_permission(
        "memorial", "transfers.read", "transfers.manage",
    ))],
)
async def get_transfer(
    tid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TransfersService.get_transfer(db, org_id, tid)


@router.post(
    "",
    response_model=TransferResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "transfers.manage"))],
)
async def create_transfer(
    data: TransferCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await TransfersService.create_transfer(db, org_id, data, _user_uuid(user))


@router.patch(
    "/{tid}",
    response_model=TransferResponse,
    dependencies=[Depends(require_permission("memorial", "transfers.manage"))],
)
async def update_transfer(
    tid: uuid.UUID,
    data: TransferUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TransfersService.update_transfer(db, org_id, tid, data)


@router.post(
    "/{tid}/transition",
    response_model=TransferResponse,
    dependencies=[Depends(require_permission("memorial", "transfers.manage"))],
)
async def transition(
    tid: uuid.UUID,
    req: TransferTransitionRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TransfersService.transition(db, org_id, tid, req)


@router.delete(
    "/{tid}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("memorial", "transfers.manage"))],
)
async def delete_transfer(
    tid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await TransfersService.delete_transfer(db, org_id, tid)
