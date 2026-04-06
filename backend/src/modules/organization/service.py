"""Business logic for organizations, memberships, and invitations."""

import secrets
import uuid
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from src.modules.organization.models import Invitation, Membership, Organization
from src.modules.organization.schemas import (
    InviteMemberRequest,
    MemberResponse,
    OrganizationUpdate,
    UpdateMemberRoleRequest,
)


class OrganizationService:
    """Stateless service layer for organization operations."""

    # ------------------------------------------------------------------
    # Organization
    # ------------------------------------------------------------------

    @staticmethod
    async def get_organization(db: AsyncSession, org_id: uuid.UUID) -> Organization:
        """Return the organization for the given ID."""
        result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = result.scalar_one_or_none()
        if org is None:
            raise NotFoundError("Organization not found.")
        return org

    @staticmethod
    async def update_organization(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: OrganizationUpdate,
    ) -> Organization:
        """Apply partial updates to the organization."""
        result = await db.execute(
            select(Organization).where(Organization.id == org_id)
        )
        org = result.scalar_one_or_none()
        if org is None:
            raise NotFoundError("Organization not found.")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if field == "settings" and isinstance(value, dict):
                # Merge settings instead of replacing them
                merged = {**(org.settings or {}), **value}
                setattr(org, field, merged)
            else:
                setattr(org, field, value)

        await db.flush()
        await db.refresh(org)
        return org

    # ------------------------------------------------------------------
    # Members
    # ------------------------------------------------------------------

    @staticmethod
    async def list_members(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[MemberResponse]:
        """List all members of the organization, joined with user data."""
        from src.modules.auth.models import User

        stmt = (
            select(
                Membership.id,
                Membership.user_id,
                Membership.organization_id,
                User.email,
                User.name,
                Membership.role,
                Membership.joined_at,
                Membership.created_at,
            )
            .join(User, User.id == Membership.user_id)
            .where(Membership.organization_id == org_id)
            .order_by(Membership.created_at)
        )
        result = await db.execute(stmt)
        rows = result.all()
        return [
            MemberResponse(
                id=row.id,
                user_id=row.user_id,
                organization_id=row.organization_id,
                email=row.email,
                name=row.name,
                role=row.role,
                joined_at=row.joined_at,
                created_at=row.created_at,
            )
            for row in rows
        ]

    @staticmethod
    async def invite_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        invited_by: uuid.UUID,
        data: InviteMemberRequest,
    ) -> Invitation:
        """Create an invitation for a new member."""
        from src.modules.auth.models import User

        # Check if user is already a member.
        existing_user = await db.execute(
            select(User).where(User.email == data.email)
        )
        user = existing_user.scalar_one_or_none()
        if user is not None:
            existing_membership = await db.execute(
                select(Membership).where(
                    Membership.organization_id == org_id,
                    Membership.user_id == user.id,
                )
            )
            if existing_membership.scalar_one_or_none() is not None:
                raise ConflictError("User is already a member of this organization.")

        # Check for a pending invitation.
        pending = await db.execute(
            select(Invitation).where(
                Invitation.organization_id == org_id,
                Invitation.email == data.email,
                Invitation.status == "pending",
                Invitation.expires_at > datetime.now(UTC),
            )
        )
        if pending.scalar_one_or_none() is not None:
            raise ConflictError(
                "A pending invitation already exists for this email address."
            )

        invitation = Invitation(
            organization_id=org_id,
            email=data.email,
            role=data.role,
            invited_by=invited_by,
            token=secrets.token_urlsafe(48),
            expires_at=datetime.now(UTC) + timedelta(days=7),
        )
        db.add(invitation)
        await db.flush()
        await db.refresh(invitation)
        return invitation

    @staticmethod
    async def update_member_role(
        db: AsyncSession,
        org_id: uuid.UUID,
        membership_id: uuid.UUID,
        data: UpdateMemberRoleRequest,
        current_user_id: uuid.UUID,
        current_user_role: str,
    ) -> Membership:
        """Change a member's role within the organization."""
        result = await db.execute(
            select(Membership).where(
                Membership.id == membership_id,
                Membership.organization_id == org_id,
            )
        )
        membership = result.scalar_one_or_none()
        if membership is None:
            raise NotFoundError("Membership not found.")

        if membership.user_id == current_user_id:
            raise ForbiddenError("You cannot change your own role.")

        if data.role == "owner" and current_user_role != "owner":
            raise ForbiddenError("Only an owner can promote a member to owner.")
        if membership.role == "owner" and current_user_role != "owner":
            raise ForbiddenError("Only an owner can change another owner's role.")

        membership.role = data.role
        await db.flush()
        await db.refresh(membership)
        return membership

    @staticmethod
    async def remove_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        membership_id: uuid.UUID,
        current_user_id: uuid.UUID,
    ) -> None:
        """Remove a member from the organization."""
        result = await db.execute(
            select(Membership).where(
                Membership.id == membership_id,
                Membership.organization_id == org_id,
            )
        )
        membership = result.scalar_one_or_none()
        if membership is None:
            raise NotFoundError("Membership not found.")

        if membership.role == "owner":
            raise ForbiddenError("Cannot remove the organization owner.")

        if membership.user_id == current_user_id:
            raise ForbiddenError(
                "Cannot remove yourself. Use the leave endpoint instead."
            )

        await db.delete(membership)
        await db.flush()

    # ------------------------------------------------------------------
    # Invitations
    # ------------------------------------------------------------------

    @staticmethod
    async def accept_invitation(db: AsyncSession, token: str) -> dict:
        """Accept an invitation using its secure token."""
        from src.modules.auth.models import User
        from src.core.security import hash_password

        result = await db.execute(
            select(Invitation).where(Invitation.token == token)
        )
        invitation = result.scalar_one_or_none()
        if invitation is None:
            raise NotFoundError("Invitation not found or invalid token.")

        if invitation.status != "pending":
            raise ConflictError(f"This invitation has already been {invitation.status}.")

        if invitation.expires_at < datetime.now(UTC):
            invitation.status = "expired"
            await db.flush()
            raise ForbiddenError("This invitation has expired.")

        # Find existing user or create a placeholder.
        user_result = await db.execute(
            select(User).where(User.email == invitation.email)
        )
        user = user_result.scalar_one_or_none()
        if user is None:
            user = User(
                name=invitation.email.split("@")[0],
                email=invitation.email,
                password_hash=hash_password(secrets.token_urlsafe(32)),
            )
            db.add(user)
            await db.flush()

        # Check if membership already exists.
        existing = await db.execute(
            select(Membership).where(
                Membership.organization_id == invitation.organization_id,
                Membership.user_id == user.id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("User is already a member of this organization.")

        membership = Membership(
            organization_id=invitation.organization_id,
            user_id=user.id,
            role=invitation.role,
        )
        db.add(membership)

        invitation.status = "accepted"
        invitation.accepted_at = datetime.now(UTC)
        await db.flush()

        # Fetch organization info.
        org_result = await db.execute(
            select(Organization).where(Organization.id == invitation.organization_id)
        )
        org = org_result.scalar_one_or_none()

        return {
            "message": "Invitation accepted successfully.",
            "organization_id": str(invitation.organization_id),
            "organization_name": org.name if org else None,
            "role": invitation.role,
            "user_id": str(user.id),
        }
