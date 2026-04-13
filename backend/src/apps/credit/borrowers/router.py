"""SavvyCredit borrowers REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.credit.borrowers.schemas import (
    BorrowerCreate,
    BorrowerListParams,
    BorrowerResponse,
    BorrowerUpdate,
)
from src.apps.credit.borrowers.service import BorrowerService

router = APIRouter(
    prefix="/borrowers",
    tags=["Credit Borrowers"],
    dependencies=[Depends(require_permission("credit", "loans.create", "loans.approve", "reports.view"))],
)
_CREATE = [Depends(require_permission("credit", "loans.create"))]


@router.get("", response_model=dict)
async def list_borrowers(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    search: str | None = Query(None),
    risk_level: str | None = Query(None),
    status_filter: str | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Any:
    params = BorrowerListParams(
        search=search, risk_level=risk_level, status=status_filter,
        page=page, page_size=page_size,
    )
    items, total = await BorrowerService.list_borrowers(db, org_id, params)
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post("", response_model=BorrowerResponse, status_code=status.HTTP_201_CREATED, dependencies=_CREATE)
async def create_borrower(
    data: BorrowerCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await BorrowerService.create_borrower(db, org_id, data)


@router.get("/{borrower_id}", response_model=BorrowerResponse)
async def get_borrower(
    borrower_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await BorrowerService.get_borrower(db, org_id, borrower_id)


@router.patch("/{borrower_id}", response_model=BorrowerResponse, dependencies=_CREATE)
async def update_borrower(
    borrower_id: uuid.UUID,
    data: BorrowerUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await BorrowerService.update_borrower(db, org_id, borrower_id, data)
