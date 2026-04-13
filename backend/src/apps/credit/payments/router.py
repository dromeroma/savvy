"""SavvyCredit payments REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.credit.payments.schemas import PaymentCreate, PaymentResponse, PenaltyResponse
from src.apps.credit.payments.service import PaymentService

router = APIRouter(
    prefix="/payments",
    tags=["Credit Payments"],
    dependencies=[Depends(require_permission("credit", "payments.write", "reports.view"))],
)
_WRITE = [Depends(require_permission("credit", "payments.write"))]


@router.post("", response_model=PaymentResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def record_payment(
    data: PaymentCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PaymentService.record_payment(db, org_id, data)


@router.get("/loan/{loan_id}", response_model=list[PaymentResponse])
async def list_payments(
    loan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PaymentService.list_payments(db, org_id, loan_id)


@router.get("/loan/{loan_id}/penalties", response_model=list[PenaltyResponse])
async def list_penalties(
    loan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PaymentService.list_penalties(db, org_id, loan_id)
