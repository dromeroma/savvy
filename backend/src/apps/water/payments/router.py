"""Payments REST endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.payments.schemas import (
    PaymentCreate,
    PaymentListItem,
    PaymentResponse,
)
from src.apps.water.payments.service import PaymentsService
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/payments", tags=["Water · Pagos"])


@router.get(
    "",
    response_model=list[PaymentListItem],
    dependencies=[Depends(require_permission("water", "payments.read", "payments.manage"))],
)
async def list_payments(
    subscriber_id: uuid.UUID | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    method: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PaymentsService.list_payments(
        db, org_id, subscriber_id=subscriber_id, date_from=date_from,
        date_to=date_to, method=method, limit=limit, offset=offset,
    )


@router.get(
    "/{payment_id}",
    response_model=PaymentResponse,
    dependencies=[Depends(require_permission("water", "payments.read", "payments.manage"))],
)
async def get_payment(
    payment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PaymentsService.get_payment(db, org_id, payment_id)


@router.post(
    "",
    response_model=PaymentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "payments.manage"))],
)
async def register_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PaymentsService.register_payment(
        db, org_id, data, collector_user_id=uuid.UUID(user["sub"]),
    )
