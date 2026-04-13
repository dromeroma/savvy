"""SavvyCredit applications REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.credit.applications.schemas import (
    ApplicationCreate,
    ApplicationDecision,
    ApplicationResponse,
)
from src.apps.credit.applications.service import ApplicationService

router = APIRouter(
    prefix="/applications",
    tags=["Credit Applications"],
    dependencies=[Depends(require_permission("credit", "loans.create", "loans.approve", "reports.view"))],
)
_CREATE = [Depends(require_permission("credit", "loans.create"))]
_APPROVE = [Depends(require_permission("credit", "loans.approve"))]


@router.get("", response_model=list[ApplicationResponse])
async def list_applications(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ApplicationService.list_applications(db, org_id, status_filter)


@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED, dependencies=_CREATE)
async def create_application(
    data: ApplicationCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ApplicationService.create_application(db, org_id, data)


@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_application(
    app_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ApplicationService.get_application(db, org_id, app_id)


@router.post("/{app_id}/decide", response_model=ApplicationResponse, dependencies=_APPROVE)
async def decide_application(
    app_id: uuid.UUID,
    data: ApplicationDecision,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ApplicationService.decide_application(db, org_id, app_id, data)
