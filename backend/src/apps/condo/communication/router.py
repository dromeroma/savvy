"""Condo communication REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.condo.communication.schemas import AnnouncementCreate, AnnouncementResponse
from src.apps.condo.communication.service import CommunicationService

router = APIRouter(prefix="/announcements", tags=["Condo Communication"])

@router.get("", response_model=list[AnnouncementResponse])
async def list_announcements(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CommunicationService.list_announcements(db, org_id)

@router.post("", response_model=AnnouncementResponse, status_code=status.HTTP_201_CREATED)
async def create_announcement(data: AnnouncementCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CommunicationService.create_announcement(db, org_id, data)
