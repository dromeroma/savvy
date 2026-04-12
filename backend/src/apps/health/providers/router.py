"""Health providers REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.health.providers.schemas import ProviderCreate, ProviderResponse
from src.apps.health.providers.service import ProviderService

router = APIRouter(prefix="/providers", tags=["Health Providers"])

@router.get("", response_model=list[ProviderResponse])
async def list_providers(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ProviderService.list_providers(db, org_id)

@router.post("", response_model=ProviderResponse, status_code=status.HTTP_201_CREATED)
async def create_provider(data: ProviderCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ProviderService.create_provider(db, org_id, data)
