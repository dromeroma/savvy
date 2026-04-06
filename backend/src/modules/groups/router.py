"""FastAPI router for organizational scopes, group types, groups, and memberships."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id, require_role
from src.modules.groups.schemas import (
    GroupCreate,
    GroupMemberAdd,
    GroupMemberResponse,
    GroupResponse,
    GroupTypeCreate,
    GroupTypeResponse,
    GroupUpdate,
    ScopeCreate,
    ScopeLeaderCreate,
    ScopeLeaderResponse,
    ScopeResponse,
    ScopeUpdate,
)
from src.modules.groups.service import GroupsService

router = APIRouter(prefix="/groups", tags=["Groups"])


# ---------------------------------------------------------------------------
# Organizational Scopes
# ---------------------------------------------------------------------------


@router.get(
    "/scopes",
    response_model=list[ScopeResponse],
    dependencies=[Depends(require_role("member", "admin", "owner"))],
)
async def list_scopes(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List all organizational scopes."""
    return await GroupsService.list_scopes(db, org_id)


@router.post(
    "/scopes",
    response_model=ScopeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def create_scope(
    data: ScopeCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Create a new organizational scope."""
    return await GroupsService.create_scope(db, org_id, data)


@router.get(
    "/scopes/{scope_id}",
    response_model=ScopeResponse,
    dependencies=[Depends(require_role("member", "admin", "owner"))],
)
async def get_scope(
    scope_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Get a single organizational scope by ID."""
    return await GroupsService.get_scope(db, org_id, scope_id)


@router.patch(
    "/scopes/{scope_id}",
    response_model=ScopeResponse,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def update_scope(
    scope_id: uuid.UUID,
    data: ScopeUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Update an organizational scope."""
    return await GroupsService.update_scope(db, org_id, scope_id, data)


@router.get(
    "/scopes/{scope_id}/leaders",
    response_model=list[ScopeLeaderResponse],
    dependencies=[Depends(require_role("member", "admin", "owner"))],
)
async def list_scope_leaders(
    scope_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List all leaders for a scope."""
    return await GroupsService.get_scope_leaders(db, org_id, scope_id)


@router.post(
    "/scopes/{scope_id}/leaders",
    response_model=ScopeLeaderResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def add_scope_leader(
    scope_id: uuid.UUID,
    data: ScopeLeaderCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Assign a leader to a scope."""
    return await GroupsService.add_scope_leader(db, org_id, scope_id, data)


@router.delete(
    "/scopes/{scope_id}/leaders/{leader_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def remove_scope_leader(
    scope_id: uuid.UUID,
    leader_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    """Remove a leader assignment from a scope."""
    await GroupsService.remove_scope_leader(db, org_id, scope_id, leader_id)


# ---------------------------------------------------------------------------
# Group Types
# ---------------------------------------------------------------------------


@router.get(
    "/types",
    response_model=list[GroupTypeResponse],
    dependencies=[Depends(require_role("member", "admin", "owner"))],
)
async def list_group_types(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List all group types for the organization."""
    return await GroupsService.list_group_types(db, org_id)


@router.post(
    "/types",
    response_model=GroupTypeResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def create_group_type(
    data: GroupTypeCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Create a new group type."""
    return await GroupsService.create_group_type(db, org_id, data)


# ---------------------------------------------------------------------------
# Groups
# ---------------------------------------------------------------------------


@router.get(
    "/",
    response_model=list[GroupResponse],
    dependencies=[Depends(require_role("member", "admin", "owner"))],
)
async def list_groups(
    type_code: str | None = Query(None, description="Filter by group type code"),
    scope_id: uuid.UUID | None = Query(None, description="Filter by scope ID"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List groups, optionally filtered by type or scope."""
    return await GroupsService.list_groups(db, org_id, type_code=type_code, scope_id=scope_id)


@router.post(
    "/",
    response_model=GroupResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def create_group(
    data: GroupCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Create a new group."""
    return await GroupsService.create_group(db, org_id, data)


@router.get(
    "/{group_id}",
    response_model=GroupResponse,
    dependencies=[Depends(require_role("member", "admin", "owner"))],
)
async def get_group(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Get a single group by ID."""
    return await GroupsService.get_group(db, org_id, group_id)


@router.patch(
    "/{group_id}",
    response_model=GroupResponse,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def update_group(
    group_id: uuid.UUID,
    data: GroupUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Update a group."""
    return await GroupsService.update_group(db, org_id, group_id, data)


@router.get(
    "/{group_id}/members",
    response_model=list[GroupMemberResponse],
    dependencies=[Depends(require_role("member", "admin", "owner"))],
)
async def list_group_members(
    group_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List all active members of a group."""
    return await GroupsService.list_group_members(db, org_id, group_id)


@router.post(
    "/{group_id}/members",
    response_model=GroupMemberResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def add_group_member(
    group_id: uuid.UUID,
    data: GroupMemberAdd,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Add a person to a group."""
    return await GroupsService.add_member(db, org_id, group_id, data)


@router.delete(
    "/{group_id}/members/{person_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def remove_group_member(
    group_id: uuid.UUID,
    person_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    """Remove a person from a group."""
    await GroupsService.remove_member(db, org_id, group_id, person_id)
