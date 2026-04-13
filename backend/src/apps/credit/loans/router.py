"""SavvyCredit loans REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.credit.loans.schemas import (
    AmortizationResponse,
    DisburseLoan,
    DisbursementResponse,
    LoanCreate,
    LoanResponse,
)
from src.apps.credit.loans.service import LoanService

router = APIRouter(
    prefix="/loans",
    tags=["Credit Loans"],
    dependencies=[Depends(require_permission("credit", "loans.create", "loans.approve", "reports.view"))],
)
_CREATE = [Depends(require_permission("credit", "loans.create"))]
_APPROVE = [Depends(require_permission("credit", "loans.approve"))]


@router.get("", response_model=list[LoanResponse])
async def list_loans(
    borrower_id: uuid.UUID | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LoanService.list_loans(db, org_id, borrower_id, status_filter)


@router.post("", response_model=LoanResponse, status_code=status.HTTP_201_CREATED, dependencies=_CREATE)
async def create_loan(
    data: LoanCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LoanService.create_loan(db, org_id, data)


@router.get("/{loan_id}", response_model=LoanResponse)
async def get_loan(
    loan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LoanService.get_loan(db, org_id, loan_id)


@router.get("/{loan_id}/amortization", response_model=list[AmortizationResponse])
async def get_amortization(
    loan_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LoanService.get_amortization(db, loan_id)


@router.post("/{loan_id}/disburse", response_model=DisbursementResponse, dependencies=_APPROVE)
async def disburse_loan(
    loan_id: uuid.UUID,
    data: DisburseLoan,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LoanService.disburse_loan(db, org_id, loan_id, data)
