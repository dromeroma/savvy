"""Business logic for CRM pipelines."""

from __future__ import annotations
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.crm.pipelines.models import CrmPipeline, CrmPipelineStage
from src.apps.crm.pipelines.schemas import PipelineCreate, PipelineUpdate


class PipelineService:

    @staticmethod
    async def list_pipelines(db: AsyncSession, org_id: uuid.UUID) -> list[CrmPipeline]:
        result = await db.execute(select(CrmPipeline).where(CrmPipeline.organization_id == org_id).order_by(CrmPipeline.name))
        return list(result.scalars().all())

    @staticmethod
    async def create_pipeline(db: AsyncSession, org_id: uuid.UUID, data: PipelineCreate) -> CrmPipeline:
        pipeline = CrmPipeline(
            organization_id=org_id, name=data.name, description=data.description,
            is_default=data.is_default, deal_rot_days=data.deal_rot_days, currency=data.currency,
        )
        db.add(pipeline)
        await db.flush()
        for s in data.stages:
            stage = CrmPipelineStage(
                pipeline_id=pipeline.id, name=s.name, sort_order=s.sort_order,
                probability=s.probability, color=s.color, is_won=s.is_won, is_lost=s.is_lost,
            )
            db.add(stage)
        await db.flush()
        await db.refresh(pipeline)
        return pipeline

    @staticmethod
    async def get_pipeline(db: AsyncSession, org_id: uuid.UUID, pipeline_id: uuid.UUID) -> CrmPipeline:
        result = await db.execute(select(CrmPipeline).where(CrmPipeline.id == pipeline_id, CrmPipeline.organization_id == org_id))
        p = result.scalar_one_or_none()
        if p is None:
            raise NotFoundError("Pipeline not found.")
        return p

    @staticmethod
    async def update_pipeline(db: AsyncSession, org_id: uuid.UUID, pipeline_id: uuid.UUID, data: PipelineUpdate) -> CrmPipeline:
        p = await PipelineService.get_pipeline(db, org_id, pipeline_id)
        for f, v in data.model_dump(exclude_unset=True).items():
            setattr(p, f, v)
        await db.flush()
        await db.refresh(p)
        return p
