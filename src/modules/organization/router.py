"""FastAPI router for organization management endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_current_user, get_db, get_org_id, require_role
from src.modules.organization.dependencies import get_current_user_id, get_current_user_role
from src.modules.organization.schemas import (
    InvitationResponse,
    InviteMemberRequest,
    MemberResponse,
    OrganizationResponse,
    OrganizationUpdate,
    UpdateMemberRoleRequest,
)
from src.modules.organization.service import OrganizationService

router = APIRouter(prefix="/organizations", tags=["Organizations"])


# ---------------------------------------------------------------------------
# Organization
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=OrganizationResponse,
    dependencies=[Depends(require_role("member", "admin", "owner"))],
)
async def get_current_organization(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Return the authenticated user's current organization."""
    return await OrganizationService.get_organization(db, org_id)


@router.patch(
    "/me",
    response_model=OrganizationResponse,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def update_current_organization(
    data: OrganizationUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """Update the authenticated user's current organization (admin+ only)."""
    return await OrganizationService.update_organization(db, org_id, data)


# ---------------------------------------------------------------------------
# Members
# ---------------------------------------------------------------------------


@router.get(
    "/members",
    response_model=list[MemberResponse],
    dependencies=[Depends(require_role("member", "admin", "owner"))],
)
async def list_members(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    """List all members of the current organization."""
    return await OrganizationService.list_members(db, org_id)


@router.post(
    "/members/invite",
    response_model=InvitationResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def invite_member(
    data: InviteMemberRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    current_user_id: str = Depends(get_current_user_id),
) -> Any:
    """Invite a new member to the organization (admin+ only)."""
    return await OrganizationService.invite_member(
        db, org_id, uuid.UUID(current_user_id), data
    )


@router.patch(
    "/members/{membership_id}/role",
    response_model=MemberResponse,
    dependencies=[Depends(require_role("owner"))],
)
async def update_member_role(
    membership_id: uuid.UUID,
    data: UpdateMemberRoleRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    current_user_id: str = Depends(get_current_user_id),
    current_user_role: str = Depends(get_current_user_role),
) -> Any:
    """Change a member's role (owner only)."""
    from src.modules.auth.models import User
    from sqlalchemy import select

    membership = await OrganizationService.update_member_role(
        db, org_id, membership_id, data, uuid.UUID(current_user_id), current_user_role
    )

    # Enrich with user profile data.
    user_result = await db.execute(select(User).where(User.id == membership.user_id))
    user = user_result.scalar_one()

    return MemberResponse(
        id=membership.id,
        user_id=membership.user_id,
        organization_id=membership.organization_id,
        email=user.email,
        name=user.name,
        role=membership.role,
        joined_at=membership.joined_at,
        created_at=membership.created_at,
    )


@router.delete(
    "/members/{membership_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_role("admin", "owner"))],
)
async def remove_member(
    membership_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    current_user_id: str = Depends(get_current_user_id),
) -> None:
    """Remove a member from the organization (admin+ only)."""
    await OrganizationService.remove_member(
        db, org_id, membership_id, uuid.UUID(current_user_id)
    )


# ---------------------------------------------------------------------------
# Invitations (public)
# ---------------------------------------------------------------------------


@router.post(
    "/invitations/{token}/accept",
    status_code=status.HTTP_200_OK,
)
async def accept_invitation(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Accept an invitation using a secure token (public, no auth required)."""
    return await OrganizationService.accept_invitation(db, token)
