"""Business logic for church visitor tracking."""

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.church.visitors.models import ChurchVisitor
from src.apps.church.visitors.schemas import VisitorCreate, VisitorUpdate
from src.core.exceptions import NotFoundError


class VisitorService:

    @staticmethod
    async def list_visitors(
        db: AsyncSession, org_id: uuid.UUID,
        status: str | None = None, search: str | None = None,
    ) -> list[ChurchVisitor]:
        stmt = (
            select(ChurchVisitor)
            .where(ChurchVisitor.organization_id == org_id)
            .order_by(ChurchVisitor.visit_date.desc())
        )
        if status:
            stmt = stmt.where(ChurchVisitor.status == status)
        if search:
            term = f"%{search}%"
            stmt = stmt.where(
                ChurchVisitor.first_name.ilike(term)
                | ChurchVisitor.last_name.ilike(term)
                | ChurchVisitor.phone.ilike(term)
            )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def create_visitor(
        db: AsyncSession, org_id: uuid.UUID, data: VisitorCreate,
    ) -> ChurchVisitor:
        visitor = ChurchVisitor(
            organization_id=org_id,
            **data.model_dump(),
        )
        db.add(visitor)
        await db.flush()
        await db.refresh(visitor)
        return visitor

    @staticmethod
    async def update_visitor(
        db: AsyncSession, org_id: uuid.UUID, visitor_id: uuid.UUID, data: VisitorUpdate,
    ) -> ChurchVisitor:
        result = await db.execute(
            select(ChurchVisitor).where(
                ChurchVisitor.id == visitor_id,
                ChurchVisitor.organization_id == org_id,
            )
        )
        visitor = result.scalar_one_or_none()
        if visitor is None:
            raise NotFoundError("Visitor not found.")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(visitor, field, value)
        await db.flush()
        await db.refresh(visitor)
        return visitor

    @staticmethod
    async def convert_to_congregant(
        db: AsyncSession, org_id: uuid.UUID, visitor_id: uuid.UUID,
    ) -> ChurchVisitor:
        """Mark visitor as converted and create a congregant record."""
        from src.apps.church.congregants.schemas import CongregantCreate
        from src.apps.church.congregants.service import CongregantService

        result = await db.execute(
            select(ChurchVisitor).where(
                ChurchVisitor.id == visitor_id,
                ChurchVisitor.organization_id == org_id,
            )
        )
        visitor = result.scalar_one_or_none()
        if visitor is None:
            raise NotFoundError("Visitor not found.")

        congregant_data = CongregantCreate(
            first_name=visitor.first_name,
            last_name=visitor.last_name,
            phone=visitor.phone,
            email=visitor.email,
        )
        congregant = await CongregantService.create_congregant(db, org_id, congregant_data)
        visitor.status = "converted"
        visitor.converted_person_id = congregant.person_id
        await db.flush()
        await db.refresh(visitor)
        return visitor
