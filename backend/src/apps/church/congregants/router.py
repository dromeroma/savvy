"""Church congregants REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.church.congregants.schemas import (
    CongregantCreate,
    CongregantListParams,
    CongregantResponse,
    CongregantUpdate,
    InactivateRequest,
)
from src.apps.church.congregants.service import CongregantService

router = APIRouter(prefix="/congregants", tags=["Church Congregants"])

_READ = [Depends(require_permission("church", "members.read"))]
_WRITE = [Depends(require_permission("church", "members.write"))]
_DELETE = [Depends(require_permission("church", "members.delete", "members.write"))]


@router.get("", response_model=dict, dependencies=_READ)
async def list_congregants(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    status_filter: str | None = Query(None, alias="status"),
    search: str | None = Query(None),
    spiritual_status: str | None = Query(None),
    scope_id: uuid.UUID | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
) -> Any:
    """List church congregants with pagination."""
    params = CongregantListParams(
        status=status_filter,
        search=search,
        spiritual_status=spiritual_status,
        scope_id=scope_id,
        page=page,
        page_size=page_size,
    )
    items, total = await CongregantService.list_congregants(db, org_id, params)
    return {
        "items": items,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "",
    response_model=CongregantResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=_WRITE,
)
async def create_congregant(
    data: CongregantCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Create a new church congregant."""
    return await CongregantService.create_congregant(db, org_id, data)


@router.get("/{congregant_id}", response_model=CongregantResponse, dependencies=_READ)
async def get_congregant(
    congregant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Get a church congregant by ID."""
    return await CongregantService.get_congregant(db, org_id, congregant_id)


@router.patch("/{congregant_id}", response_model=CongregantResponse, dependencies=_WRITE)
async def update_congregant(
    congregant_id: uuid.UUID,
    data: CongregantUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Update a church congregant."""
    return await CongregantService.update_congregant(db, org_id, congregant_id, data)


@router.post("/{congregant_id}/inactivate", response_model=CongregantResponse, dependencies=_DELETE)
async def inactivate_congregant(
    congregant_id: uuid.UUID,
    data: InactivateRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Inactivate a congregant with a reason."""
    return await CongregantService.inactivate_congregant(db, org_id, congregant_id, data.reason, data.other_reason)


@router.post("/{congregant_id}/reactivate", response_model=CongregantResponse, dependencies=_WRITE)
async def reactivate_congregant(
    congregant_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Reactivate an inactive congregant."""
    return await CongregantService.reactivate_congregant(db, org_id, congregant_id)
