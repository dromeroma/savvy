"""Church visitors REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.church.visitors.schemas import VisitorCreate, VisitorResponse, VisitorUpdate
from src.apps.church.visitors.service import VisitorService

router = APIRouter(prefix="/visitors", tags=["Church Visitors"])


@router.get("/", response_model=list[VisitorResponse])
async def list_visitors(
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await VisitorService.list_visitors(db, org_id, status=status_filter, search=search)


@router.post("/", response_model=VisitorResponse, status_code=status.HTTP_201_CREATED)
async def create_visitor(
    data: VisitorCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await VisitorService.create_visitor(db, org_id, data)


@router.patch("/{visitor_id}", response_model=VisitorResponse)
async def update_visitor(
    visitor_id: uuid.UUID,
    data: VisitorUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await VisitorService.update_visitor(db, org_id, visitor_id, data)


@router.post("/{visitor_id}/convert", response_model=VisitorResponse)
async def convert_visitor(
    visitor_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Convert a visitor to a congregant."""
    return await VisitorService.convert_to_congregant(db, org_id, visitor_id)
