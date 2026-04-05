"""Business logic for church member management."""

import uuid

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError
from src.apps.church.members.models import ChurchMember
from src.apps.church.members.schemas import (
    ChurchMemberCreate,
    ChurchMemberListParams,
    ChurchMemberUpdate,
)


class ChurchMemberService:
    """CRUD operations for church members (congregants)."""

    @staticmethod
    async def list_members(
        db: AsyncSession,
        org_id: uuid.UUID,
        params: ChurchMemberListParams,
    ) -> tuple[list[ChurchMember], int]:
        """List members with pagination and optional filters. Returns (members, total)."""
        base = select(ChurchMember).where(
            ChurchMember.organization_id == org_id,
            ChurchMember.deleted_at.is_(None),
        )

        if params.status:
            base = base.where(ChurchMember.status == params.status)

        if params.search:
            term = f"%{params.search}%"
            base = base.where(
                or_(
                    ChurchMember.first_name.ilike(term),
                    ChurchMember.last_name.ilike(term),
                    ChurchMember.email.ilike(term),
                    ChurchMember.phone.ilike(term),
                )
            )

        # Total count
        count_result = await db.execute(
            select(func.count()).select_from(base.subquery())
        )
        total = count_result.scalar() or 0

        # Paginated results
        offset = (params.page - 1) * params.page_size
        result = await db.execute(
            base.order_by(ChurchMember.last_name, ChurchMember.first_name)
            .offset(offset)
            .limit(params.page_size)
        )
        return list(result.scalars().all()), total

    @staticmethod
    async def get_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        member_id: uuid.UUID,
    ) -> ChurchMember:
        """Get a single member by ID."""
        result = await db.execute(
            select(ChurchMember).where(
                ChurchMember.id == member_id,
                ChurchMember.organization_id == org_id,
                ChurchMember.deleted_at.is_(None),
            )
        )
        member = result.scalar_one_or_none()
        if member is None:
            raise NotFoundError("Church member not found.")
        return member

    @staticmethod
    async def create_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: ChurchMemberCreate,
    ) -> ChurchMember:
        """Create a new church member."""
        # Check email uniqueness within org if provided
        if data.email:
            existing = await db.execute(
                select(ChurchMember).where(
                    ChurchMember.organization_id == org_id,
                    ChurchMember.email == data.email,
                    ChurchMember.deleted_at.is_(None),
                )
            )
            if existing.scalar_one_or_none() is not None:
                raise ConflictError("A member with this email already exists in this church.")

        member = ChurchMember(
            organization_id=org_id,
            **data.model_dump(),
        )
        db.add(member)
        await db.flush()
        await db.refresh(member)
        return member

    @staticmethod
    async def update_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        member_id: uuid.UUID,
        data: ChurchMemberUpdate,
    ) -> ChurchMember:
        """Update a church member."""
        member = await ChurchMemberService.get_member(db, org_id, member_id)

        update_data = data.model_dump(exclude_unset=True)

        # Check email uniqueness if changing email
        new_email = update_data.get("email")
        if new_email and new_email != member.email:
            existing = await db.execute(
                select(ChurchMember).where(
                    ChurchMember.organization_id == org_id,
                    ChurchMember.email == new_email,
                    ChurchMember.id != member_id,
                    ChurchMember.deleted_at.is_(None),
                )
            )
            if existing.scalar_one_or_none() is not None:
                raise ConflictError("A member with this email already exists.")

        for field, value in update_data.items():
            setattr(member, field, value)

        await db.flush()
        await db.refresh(member)
        return member

    @staticmethod
    async def delete_member(
        db: AsyncSession,
        org_id: uuid.UUID,
        member_id: uuid.UUID,
    ) -> None:
        """Soft delete a church member."""
        from datetime import UTC, datetime

        member = await ChurchMemberService.get_member(db, org_id, member_id)
        member.deleted_at = datetime.now(UTC)
        await db.flush()
