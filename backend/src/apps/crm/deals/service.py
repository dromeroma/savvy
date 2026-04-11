"""Business logic for CRM deals."""

from __future__ import annotations
import uuid
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.crm.deals.models import CrmDeal, CrmDealStageHistory
from src.apps.crm.deals.schemas import DealCreate, DealUpdate
from src.apps.crm.pipelines.models import CrmPipelineStage


class DealService:

    @staticmethod
    async def list_deals(
        db: AsyncSession, org_id: uuid.UUID,
        pipeline_id: uuid.UUID | None = None, status_filter: str | None = None,
    ) -> list[CrmDeal]:
        q = select(CrmDeal).where(CrmDeal.organization_id == org_id)
        if pipeline_id:
            q = q.where(CrmDeal.pipeline_id == pipeline_id)
        if status_filter:
            q = q.where(CrmDeal.status == status_filter)
        return list((await db.execute(q.order_by(CrmDeal.created_at.desc()))).scalars().all())

    @staticmethod
    async def create_deal(db: AsyncSession, org_id: uuid.UUID, data: DealCreate) -> CrmDeal:
        # Get stage probability
        stage_result = await db.execute(select(CrmPipelineStage).where(CrmPipelineStage.id == data.stage_id))
        stage = stage_result.scalar_one_or_none()
        probability = stage.probability if stage else 0

        deal = CrmDeal(
            organization_id=org_id, pipeline_id=data.pipeline_id, stage_id=data.stage_id,
            contact_id=data.contact_id, company_id=data.company_id, lead_id=data.lead_id,
            title=data.title, value=data.value, probability=probability,
            expected_close_date=data.expected_close_date, source=data.source, notes=data.notes,
        )
        db.add(deal)
        await db.flush()

        # Record initial stage
        history = CrmDealStageHistory(deal_id=deal.id, to_stage_id=data.stage_id)
        db.add(history)
        await db.flush()
        await db.refresh(deal)
        return deal

    @staticmethod
    async def get_deal(db: AsyncSession, org_id: uuid.UUID, deal_id: uuid.UUID) -> CrmDeal:
        result = await db.execute(select(CrmDeal).where(CrmDeal.id == deal_id, CrmDeal.organization_id == org_id))
        deal = result.scalar_one_or_none()
        if deal is None:
            raise NotFoundError("Deal not found.")
        return deal

    @staticmethod
    async def update_deal(db: AsyncSession, org_id: uuid.UUID, deal_id: uuid.UUID, data: DealUpdate) -> CrmDeal:
        deal = await DealService.get_deal(db, org_id, deal_id)
        update = data.model_dump(exclude_unset=True)

        # Track stage change
        if "stage_id" in update and update["stage_id"] != deal.stage_id:
            new_stage_id = update["stage_id"]
            history = CrmDealStageHistory(deal_id=deal.id, from_stage_id=deal.stage_id, to_stage_id=new_stage_id)
            db.add(history)

            # Update probability from stage
            stage_result = await db.execute(select(CrmPipelineStage).where(CrmPipelineStage.id == new_stage_id))
            stage = stage_result.scalar_one_or_none()
            if stage:
                deal.probability = stage.probability
                if stage.is_won:
                    deal.status = "won"
                    deal.won_date = date.today()
                elif stage.is_lost:
                    deal.status = "lost"
                    deal.lost_date = date.today()

        # Handle manual won/lost
        if "status" in update:
            if update["status"] == "won":
                deal.won_date = date.today()
            elif update["status"] == "lost":
                deal.lost_date = date.today()

        for f, v in update.items():
            setattr(deal, f, v)
        await db.flush()
        await db.refresh(deal)
        return deal

    @staticmethod
    async def get_stage_history(db: AsyncSession, deal_id: uuid.UUID) -> list[CrmDealStageHistory]:
        result = await db.execute(
            select(CrmDealStageHistory).where(CrmDealStageHistory.deal_id == deal_id)
            .order_by(CrmDealStageHistory.moved_at)
        )
        return list(result.scalars().all())
