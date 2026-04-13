"""CRM activities REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.crm.activities.schemas import ActivityCreate, ActivityResponse, ActivityUpdate
from src.apps.crm.activities.service import ActivityService

router = APIRouter(
    prefix="/activities",
    tags=["CRM Activities"],
    dependencies=[Depends(require_permission("crm", "deals.write", "contacts.write", "reports.view"))],
)
_WRITE = [Depends(require_permission("crm", "deals.write", "contacts.write"))]

@router.get("", response_model=list[ActivityResponse])
async def list_activities(
    contact_id: uuid.UUID | None = Query(None), deal_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ActivityService.list_activities(db, org_id, contact_id, deal_id)

@router.post("", response_model=ActivityResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_activity(data: ActivityCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ActivityService.create_activity(db, org_id, data)

@router.patch("/{activity_id}", response_model=ActivityResponse, dependencies=_WRITE)
async def update_activity(activity_id: uuid.UUID, data: ActivityUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ActivityService.update_activity(db, org_id, activity_id, data)
