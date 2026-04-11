"""SavvyEdu configuration REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.edu.config.schemas import (
    AcademicPeriodTypeCreate,
    AcademicPeriodTypeResponse,
    AcademicPeriodTypeUpdate,
    EvaluationTemplateCreate,
    EvaluationTemplateResponse,
    EvaluationTemplateUpdate,
    GradingSystemCreate,
    GradingSystemResponse,
    GradingSystemUpdate,
)
from src.apps.edu.config.service import EduConfigService

router = APIRouter(prefix="/config", tags=["Edu Config"])


# ---------------------------------------------------------------------------
# Grading Systems
# ---------------------------------------------------------------------------


@router.get("/grading-systems", response_model=list[GradingSystemResponse])
async def list_grading_systems(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduConfigService.list_grading_systems(db, org_id)


@router.post(
    "/grading-systems",
    response_model=GradingSystemResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_grading_system(
    data: GradingSystemCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduConfigService.create_grading_system(db, org_id, data)


@router.get("/grading-systems/{gs_id}", response_model=GradingSystemResponse)
async def get_grading_system(
    gs_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduConfigService.get_grading_system(db, org_id, gs_id)


@router.patch("/grading-systems/{gs_id}", response_model=GradingSystemResponse)
async def update_grading_system(
    gs_id: uuid.UUID,
    data: GradingSystemUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduConfigService.update_grading_system(db, org_id, gs_id, data)


@router.delete("/grading-systems/{gs_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_grading_system(
    gs_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await EduConfigService.delete_grading_system(db, org_id, gs_id)


# ---------------------------------------------------------------------------
# Academic Period Types
# ---------------------------------------------------------------------------


@router.get("/period-types", response_model=list[AcademicPeriodTypeResponse])
async def list_period_types(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduConfigService.list_period_types(db, org_id)


@router.post(
    "/period-types",
    response_model=AcademicPeriodTypeResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_period_type(
    data: AcademicPeriodTypeCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduConfigService.create_period_type(db, org_id, data)


@router.patch("/period-types/{pt_id}", response_model=AcademicPeriodTypeResponse)
async def update_period_type(
    pt_id: uuid.UUID,
    data: AcademicPeriodTypeUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduConfigService.update_period_type(db, org_id, pt_id, data)


# ---------------------------------------------------------------------------
# Evaluation Templates
# ---------------------------------------------------------------------------


@router.get("/evaluation-templates", response_model=list[EvaluationTemplateResponse])
async def list_evaluation_templates(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduConfigService.list_evaluation_templates(db, org_id)


@router.post(
    "/evaluation-templates",
    response_model=EvaluationTemplateResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_evaluation_template(
    data: EvaluationTemplateCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduConfigService.create_evaluation_template(db, org_id, data)


@router.patch("/evaluation-templates/{et_id}", response_model=EvaluationTemplateResponse)
async def update_evaluation_template(
    et_id: uuid.UUID,
    data: EvaluationTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduConfigService.update_evaluation_template(db, org_id, et_id, data)
