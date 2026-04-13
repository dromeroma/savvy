"""CRM leads REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.crm.leads.schemas import LeadCreate, LeadResponse, LeadUpdate
from src.apps.crm.leads.service import LeadService

router = APIRouter(
    prefix="/leads",
    tags=["CRM Leads"],
    dependencies=[Depends(require_permission("crm", "leads.assign", "contacts.write", "deals.write", "reports.view"))],
)
_WRITE = [Depends(require_permission("crm", "leads.assign", "contacts.write"))]

@router.get("", response_model=list[LeadResponse])
async def list_leads(status_filter: str | None = Query(None, alias="status"), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LeadService.list_leads(db, org_id, status_filter)

@router.post("", response_model=LeadResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_lead(data: LeadCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LeadService.create_lead(db, org_id, data)

@router.get("/{lead_id}", response_model=LeadResponse)
async def get_lead(lead_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LeadService.get_lead(db, org_id, lead_id)

@router.patch("/{lead_id}", response_model=LeadResponse, dependencies=_WRITE)
async def update_lead(lead_id: uuid.UUID, data: LeadUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await LeadService.update_lead(db, org_id, lead_id, data)
