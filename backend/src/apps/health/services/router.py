"""Health services REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.health.services.schemas import ServiceCreate, ServiceResponse
from src.apps.health.services.service import HealthServiceCatalog

router = APIRouter(
    prefix="/services",
    tags=["Health Services"],
    dependencies=[Depends(require_permission("health", "services.write", "reports.view"))],
)

@router.get("", response_model=list[ServiceResponse])
async def list_services(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await HealthServiceCatalog.list_services(db, org_id)

@router.post("", response_model=ServiceResponse, status_code=status.HTTP_201_CREATED)
async def create_service(data: ServiceCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await HealthServiceCatalog.create_service(db, org_id, data)
