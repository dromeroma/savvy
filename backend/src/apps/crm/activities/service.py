"""Business logic for CRM activities."""

from __future__ import annotations
import uuid
from datetime import UTC, datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.crm.activities.models import CrmActivity
from src.apps.crm.activities.schemas import ActivityCreate, ActivityUpdate


class ActivityService:

    @staticmethod
    async def list_activities(
        db: AsyncSession, org_id: uuid.UUID,
        contact_id: uuid.UUID | None = None, deal_id: uuid.UUID | None = None,
    ) -> list[CrmActivity]:
        q = select(CrmActivity).where(CrmActivity.organization_id == org_id)
        if contact_id:
            q = q.where(CrmActivity.contact_id == contact_id)
        if deal_id:
            q = q.where(CrmActivity.deal_id == deal_id)
        return list((await db.execute(q.order_by(CrmActivity.created_at.desc()))).scalars().all())

    @staticmethod
    async def create_activity(db: AsyncSession, org_id: uuid.UUID, data: ActivityCreate) -> CrmActivity:
        activity = CrmActivity(
            organization_id=org_id, type=data.type, subject=data.subject,
            description=data.description, contact_id=data.contact_id,
            deal_id=data.deal_id, due_date=data.due_date,
        )
        db.add(activity)
        await db.flush()
        await db.refresh(activity)
        return activity

    @staticmethod
    async def update_activity(db: AsyncSession, org_id: uuid.UUID, activity_id: uuid.UUID, data: ActivityUpdate) -> CrmActivity:
        result = await db.execute(select(CrmActivity).where(CrmActivity.id == activity_id, CrmActivity.organization_id == org_id))
        activity = result.scalar_one_or_none()
        if activity is None:
            raise NotFoundError("Activity not found.")
        update = data.model_dump(exclude_unset=True)
        if "completed" in update and update["completed"] and not activity.completed:
            activity.completed_at = datetime.now(UTC)
        for f, v in update.items():
            setattr(activity, f, v)
        await db.flush()
        await db.refresh(activity)
        return activity
