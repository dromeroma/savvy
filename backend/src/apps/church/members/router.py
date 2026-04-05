"""Church members REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.church.members.schemas import (
    ChurchMemberCreate,
    ChurchMemberListParams,
    ChurchMemberResponse,
    ChurchMemberUpdate,
)
from src.apps.church.members.service import ChurchMemberService

router = APIRouter(prefix="/members", tags=["Church Members"])


@router.get("", response_model=dict)
async def list_members(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Any:
    """List church members with pagination."""
    params = ChurchMemberListParams(
        status=status_filter, search=search, page=page, page_size=page_size,
    )
    members, total = await ChurchMemberService.list_members(db, org_id, params)
    return {
        "items": [ChurchMemberResponse.model_validate(m) for m in members],
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "",
    response_model=ChurchMemberResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_member(
    data: ChurchMemberCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Create a new church member."""
    return await ChurchMemberService.create_member(db, org_id, data)


@router.get("/{member_id}", response_model=ChurchMemberResponse)
async def get_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Get a church member by ID."""
    return await ChurchMemberService.get_member(db, org_id, member_id)


@router.patch("/{member_id}", response_model=ChurchMemberResponse)
async def update_member(
    member_id: uuid.UUID,
    data: ChurchMemberUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Update a church member."""
    return await ChurchMemberService.update_member(db, org_id, member_id, data)


@router.delete(
    "/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
)
async def delete_member(
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    """Soft delete a church member."""
    await ChurchMemberService.delete_member(db, org_id, member_id)
