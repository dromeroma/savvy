"""Endpoints REST de CRM (leads + comunicaciones)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.crm.schemas import (
    CommunicationCreate,
    CommunicationResponse,
    ConvertToContract,
    ConvertToService,
    LeadCreate,
    LeadListItem,
    LeadResponse,
    LeadUpdate,
    MarkLost,
)
from src.apps.memorial.crm.service import (
    CommunicationsService,
    LeadsService,
)
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/crm", tags=["Memorial · CRM"])


def _user_uuid(user: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(user["sub"])


def _perm_read():
    return Depends(require_permission(
        "memorial", "crm.read", "crm.manage",
    ))


def _perm_manage():
    return Depends(require_permission("memorial", "crm.manage"))


# ---------------------------------------------------------------- Leads


@router.get("/leads", response_model=list[LeadListItem], dependencies=[_perm_read()])
async def list_leads(
    status_: str | None = Query(None, alias="status"),
    source: str | None = Query(None),
    assigned_to: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LeadsService.list_(
        db, org_id,
        status=status_, source=source, assigned_to=assigned_to,
        search=search, limit=limit, offset=offset,
    )


@router.get("/leads/{lid}", response_model=LeadResponse, dependencies=[_perm_read()])
async def get_lead(
    lid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LeadsService.get(db, org_id, lid)


@router.post(
    "/leads", response_model=LeadResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_manage()],
)
async def create_lead(
    data: LeadCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await LeadsService.create(db, org_id, data, _user_uuid(user))


@router.patch("/leads/{lid}", response_model=LeadResponse, dependencies=[_perm_manage()])
async def update_lead(
    lid: uuid.UUID,
    data: LeadUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LeadsService.update(db, org_id, lid, data)


@router.delete(
    "/leads/{lid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_manage()],
)
async def delete_lead(
    lid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await LeadsService.delete(db, org_id, lid)


@router.post(
    "/leads/{lid}/convert-contract", response_model=LeadResponse, dependencies=[_perm_manage()],
)
async def convert_to_contract(
    lid: uuid.UUID,
    data: ConvertToContract,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LeadsService.convert_to_contract(db, org_id, lid, data.contract_id)


@router.post(
    "/leads/{lid}/convert-service", response_model=LeadResponse, dependencies=[_perm_manage()],
)
async def convert_to_service(
    lid: uuid.UUID,
    data: ConvertToService,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LeadsService.convert_to_service(db, org_id, lid, data.service_id)


@router.post("/leads/{lid}/mark-lost", response_model=LeadResponse, dependencies=[_perm_manage()])
async def mark_lost(
    lid: uuid.UUID,
    data: MarkLost,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LeadsService.mark_lost(db, org_id, lid, data.lost_reason)


# ---------------------------------------------------------------- Communications


@router.get(
    "/leads/{lid}/communications",
    response_model=list[CommunicationResponse], dependencies=[_perm_read()],
)
async def list_communications(
    lid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await CommunicationsService.list_for_lead(db, org_id, lid)


@router.post(
    "/leads/{lid}/communications", response_model=CommunicationResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_manage()],
)
async def create_communication(
    lid: uuid.UUID,
    data: CommunicationCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await CommunicationsService.create(db, org_id, lid, data, _user_uuid(user))


@router.delete(
    "/communications/{cid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_manage()],
)
async def delete_communication(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await CommunicationsService.delete(db, org_id, cid)
