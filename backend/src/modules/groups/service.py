"""Business logic for organizational scopes, group types, groups, and memberships."""

import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError
from src.modules.groups.models import (
    Group,
    GroupMember,
    GroupType,
    OrganizationalScope,
    ScopeLeader,
)
from src.modules.groups.schemas import (
    GroupCreate,
    GroupMemberAdd,
    GroupTypeCreate,
    GroupUpdate,
    ScopeCreate,
    ScopeLeaderCreate,
    ScopeUpdate,
)


class GroupsService:
    """Stateless service layer for groups module operations."""

    # ------------------------------------------------------------------
    # Organizational Scopes
    # ------------------------------------------------------------------

    @staticmethod
    async def list_scopes(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[OrganizationalScope]:
        """List all organizational scopes for the given organization."""
        result = await db.execute(
            select(OrganizationalScope)
            .where(OrganizationalScope.organization_id == org_id)
            .order_by(OrganizationalScope.type, OrganizationalScope.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_scope(
        db: AsyncSession, org_id: uuid.UUID, data: ScopeCreate,
    ) -> OrganizationalScope:
        """Create a new organizational scope."""
        # Check uniqueness.
        existing = await db.execute(
            select(OrganizationalScope).where(
                OrganizationalScope.organization_id == org_id,
                OrganizationalScope.type == data.type,
                OrganizationalScope.code == data.code,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError(f"Scope with type '{data.type}' and code '{data.code}' already exists.")

        scope = OrganizationalScope(
            organization_id=org_id,
            **data.model_dump(),
        )
        db.add(scope)
        await db.flush()
        await db.refresh(scope)
        return scope

    @staticmethod
    async def get_scope(
        db: AsyncSession, org_id: uuid.UUID, scope_id: uuid.UUID,
    ) -> OrganizationalScope:
        """Return a single organizational scope by ID."""
        result = await db.execute(
            select(OrganizationalScope).where(
                OrganizationalScope.id == scope_id,
                OrganizationalScope.organization_id == org_id,
            )
        )
        scope = result.scalar_one_or_none()
        if scope is None:
            raise NotFoundError("Organizational scope not found.")
        return scope

    @staticmethod
    async def update_scope(
        db: AsyncSession, org_id: uuid.UUID, scope_id: uuid.UUID, data: ScopeUpdate,
    ) -> OrganizationalScope:
        """Apply partial updates to an organizational scope."""
        result = await db.execute(
            select(OrganizationalScope).where(
                OrganizationalScope.id == scope_id,
                OrganizationalScope.organization_id == org_id,
            )
        )
        scope = result.scalar_one_or_none()
        if scope is None:
            raise NotFoundError("Organizational scope not found.")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(scope, field, value)

        await db.flush()
        await db.refresh(scope)
        return scope

    # ------------------------------------------------------------------
    # Scope Leaders
    # ------------------------------------------------------------------

    @staticmethod
    async def get_scope_leaders(
        db: AsyncSession, org_id: uuid.UUID, scope_id: uuid.UUID,
    ) -> list[ScopeLeader]:
        """List all leaders for a given scope."""
        result = await db.execute(
            select(ScopeLeader).where(
                ScopeLeader.organization_id == org_id,
                ScopeLeader.scope_id == scope_id,
                ScopeLeader.ended_at.is_(None),
            )
            .order_by(ScopeLeader.started_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_scope_leader(
        db: AsyncSession,
        org_id: uuid.UUID,
        scope_id: uuid.UUID,
        data: ScopeLeaderCreate,
    ) -> ScopeLeader:
        """Assign a leader to an organizational scope."""
        # Verify scope exists.
        scope_result = await db.execute(
            select(OrganizationalScope).where(
                OrganizationalScope.id == scope_id,
                OrganizationalScope.organization_id == org_id,
            )
        )
        if scope_result.scalar_one_or_none() is None:
            raise NotFoundError("Organizational scope not found.")

        # Check uniqueness.
        existing = await db.execute(
            select(ScopeLeader).where(
                ScopeLeader.scope_id == scope_id,
                ScopeLeader.person_id == data.person_id,
                ScopeLeader.role == data.role,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("This person already holds this role in the scope.")

        leader = ScopeLeader(
            organization_id=org_id,
            scope_id=scope_id,
            **data.model_dump(),
        )
        db.add(leader)
        await db.flush()
        await db.refresh(leader)
        return leader

    @staticmethod
    async def remove_scope_leader(
        db: AsyncSession,
        org_id: uuid.UUID,
        scope_id: uuid.UUID,
        leader_id: uuid.UUID,
    ) -> None:
        """Remove a leader assignment from a scope."""
        result = await db.execute(
            select(ScopeLeader).where(
                ScopeLeader.id == leader_id,
                ScopeLeader.scope_id == scope_id,
                ScopeLeader.organization_id == org_id,
            )
        )
        leader = result.scalar_one_or_none()
        if leader is None:
            raise NotFoundError("Scope leader assignment not found.")

        await db.delete(leader)
        await db.flush()

    # ------------------------------------------------------------------
    # Group Types
    # ------------------------------------------------------------------

    @staticmethod
    async def list_group_types(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[GroupType]:
        """List all group types for the organization."""
        result = await db.execute(
            select(GroupType)
            .where(GroupType.organization_id == org_id)
            .order_by(GroupType.name)
        )
        return list(result.scalars().all())

    @staticmethod
    async def create_group_type(
        db: AsyncSession, org_id: uuid.UUID, data: GroupTypeCreate,
    ) -> GroupType:
        """Create a new group type."""
        existing = await db.execute(
            select(GroupType).where(
                GroupType.organization_id == org_id,
                GroupType.code == data.code,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError(f"Group type with code '{data.code}' already exists.")

        group_type = GroupType(
            organization_id=org_id,
            **data.model_dump(),
        )
        db.add(group_type)
        await db.flush()
        await db.refresh(group_type)
        return group_type

    # ------------------------------------------------------------------
    # Groups
    # ------------------------------------------------------------------

    @staticmethod
    async def list_groups(
        db: AsyncSession,
        org_id: uuid.UUID,
        type_code: str | None = None,
        scope_id: uuid.UUID | None = None,
    ) -> list[Group]:
        """List groups, optionally filtered by type code or scope."""
        stmt = select(Group).where(Group.organization_id == org_id)

        if type_code is not None:
            stmt = stmt.join(GroupType, Group.group_type_id == GroupType.id).where(
                GroupType.code == type_code,
            )

        if scope_id is not None:
            stmt = stmt.where(Group.scope_id == scope_id)

        stmt = stmt.order_by(Group.name)
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_group(
        db: AsyncSession, org_id: uuid.UUID, data: GroupCreate,
    ) -> Group:
        """Create a new group."""
        # Verify group type exists and belongs to org.
        gt_result = await db.execute(
            select(GroupType).where(
                GroupType.id == data.group_type_id,
                GroupType.organization_id == org_id,
            )
        )
        if gt_result.scalar_one_or_none() is None:
            raise NotFoundError("Group type not found.")

        group = Group(
            organization_id=org_id,
            **data.model_dump(),
        )
        db.add(group)
        await db.flush()
        await db.refresh(group)
        return group

    @staticmethod
    async def get_group(
        db: AsyncSession, org_id: uuid.UUID, group_id: uuid.UUID,
    ) -> Group:
        """Return a single group by ID."""
        result = await db.execute(
            select(Group).where(
                Group.id == group_id,
                Group.organization_id == org_id,
            )
        )
        group = result.scalar_one_or_none()
        if group is None:
            raise NotFoundError("Group not found.")
        return group

    @staticmethod
    async def update_group(
        db: AsyncSession, org_id: uuid.UUID, group_id: uuid.UUID, data: GroupUpdate,
    ) -> Group:
        """Apply partial updates to a group."""
        result = await db.execute(
            select(Group).where(
                Group.id == group_id,
                Group.organization_id == org_id,
            )
        )
        group = result.scalar_one_or_none()
        if group is None:
            raise NotFoundError("Group not found.")

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(group, field, value)

        await db.flush()
        await db.refresh(group)
        return group

    # ------------------------------------------------------------------
    # Group Members
    # ------------------------------------------------------------------

    @staticmethod
    async def list_group_members(
        db: AsyncSession, org_id: uuid.UUID, group_id: uuid.UUID,
    ) -> list[GroupMember]:
        """List all active members of a group."""
        result = await db.execute(
            select(GroupMember).where(
                GroupMember.organization_id == org_id,
                GroupMember.group_id == group_id,
                GroupMember.left_at.is_(None),
            )
            .order_by(GroupMember.joined_at)
        )
        return list(result.scalars().all())

    @staticmethod
    async def add_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        group_id: uuid.UUID,
        data: GroupMemberAdd,
    ) -> GroupMember:
        """Add a person to a group."""
        # Verify group exists.
        group_result = await db.execute(
            select(Group).where(
                Group.id == group_id,
                Group.organization_id == org_id,
            )
        )
        if group_result.scalar_one_or_none() is None:
            raise NotFoundError("Group not found.")

        # Check uniqueness.
        existing = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.person_id == data.person_id,
            )
        )
        if existing.scalar_one_or_none() is not None:
            raise ConflictError("This person is already a member of the group.")

        member = GroupMember(
            organization_id=org_id,
            group_id=group_id,
            **data.model_dump(),
        )
        db.add(member)
        await db.flush()
        await db.refresh(member)
        return member

    @staticmethod
    async def remove_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        group_id: uuid.UUID,
        person_id: uuid.UUID,
    ) -> None:
        """Remove a person from a group."""
        result = await db.execute(
            select(GroupMember).where(
                GroupMember.group_id == group_id,
                GroupMember.person_id == person_id,
                GroupMember.organization_id == org_id,
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise NotFoundError("Group member not found.")

        await db.delete(member)
        await db.flush()

    @staticmethod
    async def get_person_groups(
        db: AsyncSession, org_id: uuid.UUID, person_id: uuid.UUID,
    ) -> list[GroupMember]:
        """Return all active group memberships for a given person."""
        result = await db.execute(
            select(GroupMember).where(
                GroupMember.organization_id == org_id,
                GroupMember.person_id == person_id,
                GroupMember.left_at.is_(None),
            )
            .order_by(GroupMember.joined_at)
        )
        return list(result.scalars().all())
