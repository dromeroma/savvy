"""Endpoints REST de servicios funerarios."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.services.schemas import (
    AddNoteRequest,
    DashboardKpis,
    FamilyMemberCreate,
    FamilyMemberResponse,
    FamilyMemberUpdate,
    ServiceCreate,
    ServiceEventResponse,
    ServiceListItem,
    ServiceResponse,
    ServiceUpdate,
    StatusTransitionRequest,
)
from src.apps.memorial.services.service import MemorialServicesService
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/services", tags=["Memorial · Servicios"])


def _user_uuid(user: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(user["sub"])


# ---------------------------------------------------------------- Dashboard


dashboard_router = APIRouter(prefix="/dashboard", tags=["Memorial · Dashboard"])


@dashboard_router.get(
    "/kpis",
    response_model=DashboardKpis,
    dependencies=[Depends(require_permission("memorial", "dashboard.read", "services.read", "services.manage"))],
)
async def dashboard_kpis(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await MemorialServicesService.dashboard_kpis(db, org_id)


# ---------------------------------------------------------------- Services CRUD


@router.get(
    "",
    response_model=list[ServiceListItem],
    dependencies=[Depends(require_permission("memorial", "services.read", "services.manage"))],
)
async def list_services(
    search: str | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    service_type: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await MemorialServicesService.list_services(
        db, org_id,
        search=search, status=status_, service_type=service_type,
        limit=limit, offset=offset,
    )


@router.get(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[Depends(require_permission("memorial", "services.read", "services.manage"))],
)
async def get_service(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    svc, family = await MemorialServicesService.get_service_with_family(db, org_id, service_id)
    # Build response with family hydrated. Pydantic from_attributes will
    # also pick up the relationship via the model — but we want the
    # 'relationship' attr name in the schema, while the model attribute
    # is relationship_ (the column is named 'relationship' in DB).
    family_out = [
        FamilyMemberResponse(
            id=f.id, service_id=f.service_id,
            first_name=f.first_name, last_name=f.last_name,
            document_type=f.document_type, document_number=f.document_number,
            relationship=f.relationship_,
            phone=f.phone, mobile=f.mobile, email=f.email,
            address=f.address, is_primary=f.is_primary, notes=f.notes,
            created_at=f.created_at, updated_at=f.updated_at,
        )
        for f in family
    ]
    resp = ServiceResponse.model_validate(svc)
    resp.family_members = family_out
    return resp


@router.post(
    "",
    response_model=ServiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "services.manage"))],
)
async def create_service(
    data: ServiceCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    svc = await MemorialServicesService.create_service(db, org_id, data, _user_uuid(user))
    # Hidratamos como en get_service
    _, family = await MemorialServicesService.get_service_with_family(db, org_id, svc.id)
    resp = ServiceResponse.model_validate(svc)
    resp.family_members = [
        FamilyMemberResponse(
            id=f.id, service_id=f.service_id,
            first_name=f.first_name, last_name=f.last_name,
            document_type=f.document_type, document_number=f.document_number,
            relationship=f.relationship_,
            phone=f.phone, mobile=f.mobile, email=f.email,
            address=f.address, is_primary=f.is_primary, notes=f.notes,
            created_at=f.created_at, updated_at=f.updated_at,
        )
        for f in family
    ]
    return resp


@router.patch(
    "/{service_id}",
    response_model=ServiceResponse,
    dependencies=[Depends(require_permission("memorial", "services.manage"))],
)
async def update_service(
    service_id: uuid.UUID,
    data: ServiceUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    await MemorialServicesService.update_service(
        db, org_id, service_id, data, _user_uuid(user),
    )
    return await get_service(service_id, db, org_id)


@router.post(
    "/{service_id}/transition",
    response_model=ServiceResponse,
    dependencies=[Depends(require_permission("memorial", "services.manage"))],
)
async def transition_status(
    service_id: uuid.UUID,
    req: StatusTransitionRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    await MemorialServicesService.transition_status(
        db, org_id, service_id, req, _user_uuid(user),
    )
    return await get_service(service_id, db, org_id)


@router.post(
    "/{service_id}/notes",
    response_model=ServiceEventResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "services.manage"))],
)
async def add_note(
    service_id: uuid.UUID,
    data: AddNoteRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await MemorialServicesService.add_note(
        db, org_id, service_id, data, _user_uuid(user),
    )


@router.get(
    "/{service_id}/events",
    response_model=list[ServiceEventResponse],
    dependencies=[Depends(require_permission("memorial", "services.read", "services.manage"))],
)
async def list_events(
    service_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    events = await MemorialServicesService.list_events(db, org_id, service_id)
    return [ServiceEventResponse.model_validate(e) for e in events]


# ---------------------------------------------------------------- Family


@router.post(
    "/{service_id}/family",
    response_model=FamilyMemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "services.manage"))],
)
async def add_family_member(
    service_id: uuid.UUID,
    data: FamilyMemberCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    fam = await MemorialServicesService.add_family_member(
        db, org_id, service_id, data, _user_uuid(user),
    )
    return FamilyMemberResponse(
        id=fam.id, service_id=fam.service_id,
        first_name=fam.first_name, last_name=fam.last_name,
        document_type=fam.document_type, document_number=fam.document_number,
        relationship=fam.relationship_,
        phone=fam.phone, mobile=fam.mobile, email=fam.email,
        address=fam.address, is_primary=fam.is_primary, notes=fam.notes,
        created_at=fam.created_at, updated_at=fam.updated_at,
    )


@router.patch(
    "/{service_id}/family/{member_id}",
    response_model=FamilyMemberResponse,
    dependencies=[Depends(require_permission("memorial", "services.manage"))],
)
async def update_family_member(
    service_id: uuid.UUID,
    member_id: uuid.UUID,
    data: FamilyMemberUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    fam = await MemorialServicesService.update_family_member(
        db, org_id, service_id, member_id, data, _user_uuid(user),
    )
    return FamilyMemberResponse(
        id=fam.id, service_id=fam.service_id,
        first_name=fam.first_name, last_name=fam.last_name,
        document_type=fam.document_type, document_number=fam.document_number,
        relationship=fam.relationship_,
        phone=fam.phone, mobile=fam.mobile, email=fam.email,
        address=fam.address, is_primary=fam.is_primary, notes=fam.notes,
        created_at=fam.created_at, updated_at=fam.updated_at,
    )


@router.delete(
    "/{service_id}/family/{member_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("memorial", "services.manage"))],
)
async def remove_family_member(
    service_id: uuid.UUID,
    member_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> None:
    await MemorialServicesService.remove_family_member(
        db, org_id, service_id, member_id, _user_uuid(user),
    )
