"""Routes REST endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.routes.schemas import (
    CollectorRouteSummary,
    CollectorSubscriberItem,
    RouteAssignmentCreate,
    RouteAssignmentResponse,
    RouteCreate,
    RouteListItem,
    RouteResponse,
    RouteUpdate,
)
from src.apps.water.routes.service import RoutesService
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/routes", tags=["Water · Rutas"])


# ---------- Collector self-service (placed before {route_id} so paths don't clash)


@router.get(
    "/me",
    response_model=list[CollectorRouteSummary],
    summary="Rutas asignadas al cobrador autenticado",
)
async def my_routes(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await RoutesService.my_routes(db, org_id, uuid.UUID(user["sub"]))


@router.get(
    "/{route_id}/collection-view",
    response_model=list[CollectorSubscriberItem],
    summary="Vista del cobrador para una ruta (suscriptores + saldos)",
)
async def collection_view(
    route_id: uuid.UUID,
    require_collector: bool = Query(
        True,
        description="Si true, solo el cobrador asignado a la ruta puede verla.",
    ),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict = Depends(get_current_user),
) -> Any:
    return await RoutesService.route_collection_view(
        db, org_id, route_id, uuid.UUID(user["sub"]), require_collector,
    )


# ---------- Admin CRUD


@router.get(
    "",
    response_model=list[RouteListItem],
    dependencies=[Depends(require_permission("water", "routes.read", "routes.manage"))],
)
async def list_routes(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RoutesService.list_routes(db, org_id, active_only=active_only)


@router.post(
    "",
    response_model=RouteResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "routes.manage"))],
)
async def create_route(
    data: RouteCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RoutesService.create_route(db, org_id, data)


@router.get(
    "/{route_id}",
    response_model=RouteResponse,
    dependencies=[Depends(require_permission("water", "routes.read", "routes.manage"))],
)
async def get_route(
    route_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RoutesService.get_route(db, org_id, route_id)


@router.patch(
    "/{route_id}",
    response_model=RouteResponse,
    dependencies=[Depends(require_permission("water", "routes.manage"))],
)
async def update_route(
    route_id: uuid.UUID,
    data: RouteUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RoutesService.update_route(db, org_id, route_id, data)


@router.delete(
    "/{route_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("water", "routes.manage"))],
)
async def delete_route(
    route_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await RoutesService.delete_route(db, org_id, route_id)


# ---------- Assignments


@router.get(
    "/{route_id}/subscribers",
    response_model=list[RouteAssignmentResponse],
    dependencies=[Depends(require_permission("water", "routes.read", "routes.manage"))],
)
async def list_assignments(
    route_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RoutesService.list_assignments(db, org_id, route_id)


@router.post(
    "/{route_id}/subscribers",
    response_model=RouteAssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "routes.manage"))],
)
async def assign(
    route_id: uuid.UUID,
    data: RouteAssignmentCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await RoutesService.assign(db, org_id, route_id, data)


@router.delete(
    "/{route_id}/subscribers/{subscriber_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("water", "routes.manage"))],
)
async def unassign(
    route_id: uuid.UUID,
    subscriber_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await RoutesService.unassign(db, org_id, route_id, subscriber_id)
