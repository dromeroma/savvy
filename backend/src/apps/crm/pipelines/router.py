"""CRM pipelines REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.crm.pipelines.schemas import PipelineCreate, PipelineResponse, PipelineUpdate
from src.apps.crm.pipelines.service import PipelineService

router = APIRouter(
    prefix="/pipelines",
    tags=["CRM Pipelines"],
    dependencies=[Depends(require_permission("crm", "deals.write", "reports.view"))],
)
_WRITE = [Depends(require_permission("crm", "deals.write"))]

@router.get("", response_model=list[PipelineResponse])
async def list_pipelines(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PipelineService.list_pipelines(db, org_id)

@router.post("", response_model=PipelineResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_pipeline(data: PipelineCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PipelineService.create_pipeline(db, org_id, data)

@router.get("/{pipeline_id}", response_model=PipelineResponse)
async def get_pipeline(pipeline_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PipelineService.get_pipeline(db, org_id, pipeline_id)

@router.patch("/{pipeline_id}", response_model=PipelineResponse, dependencies=_WRITE)
async def update_pipeline(pipeline_id: uuid.UUID, data: PipelineUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PipelineService.update_pipeline(db, org_id, pipeline_id, data)
