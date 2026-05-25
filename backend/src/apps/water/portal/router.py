"""Portal REST endpoints — consumed by the subscriber/customer UI.

These endpoints are gated only by the customer role on the water app
(no admin permissions required). Every endpoint enforces that the data
returned belongs to the calling user's WaterSubscriber row.
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.portal.schemas import (
    PortalConsumptionItem,
    PortalDashboard,
    PortalInvoiceItem,
    PortalMe,
    PortalPaymentItem,
    PortalPqrsListItem,
    PortalPqrsResponse,
)
from src.apps.water.portal.service import PortalService
from src.apps.water.pqrs.schemas import PqrsCreate
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/portal", tags=["Water · Portal cliente"])


@router.get(
    "/me",
    response_model=PortalMe,
    dependencies=[Depends(require_permission("water", "portal.view"))],
)
async def me(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PortalService.me(db, org_id, uuid.UUID(user["sub"]))


@router.get(
    "/dashboard",
    response_model=PortalDashboard,
    dependencies=[Depends(require_permission("water", "portal.view"))],
)
async def dashboard(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PortalService.dashboard(db, org_id, uuid.UUID(user["sub"]))


@router.get(
    "/invoices",
    response_model=list[PortalInvoiceItem],
    dependencies=[Depends(require_permission("water", "portal.view"))],
)
async def invoices(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PortalService.invoices(db, org_id, uuid.UUID(user["sub"]))


@router.get(
    "/payments",
    response_model=list[PortalPaymentItem],
    dependencies=[Depends(require_permission("water", "portal.view"))],
)
async def payments(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PortalService.payments(db, org_id, uuid.UUID(user["sub"]))


@router.get(
    "/consumption",
    response_model=list[PortalConsumptionItem],
    dependencies=[Depends(require_permission("water", "portal.view"))],
)
async def consumption(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PortalService.consumption(db, org_id, uuid.UUID(user["sub"]))


# ---------- PQRS (customer-side) ----------


@router.get(
    "/pqrs",
    response_model=list[PortalPqrsListItem],
    dependencies=[Depends(require_permission("water", "portal.view"))],
)
async def list_my_pqrs(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PortalService.list_my_pqrs(db, org_id, uuid.UUID(user["sub"]))


@router.get(
    "/pqrs/{pqrs_id}",
    response_model=PortalPqrsResponse,
    dependencies=[Depends(require_permission("water", "portal.view"))],
)
async def get_my_pqrs(
    pqrs_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PortalService.get_my_pqrs(db, org_id, uuid.UUID(user["sub"]), pqrs_id)


@router.post(
    "/pqrs",
    response_model=PortalPqrsResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "portal.view"))],
)
async def create_my_pqrs(
    data: PqrsCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await PortalService.create_my_pqrs(
        db, org_id, uuid.UUID(user["sub"]), data,
    )
