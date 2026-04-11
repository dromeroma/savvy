"""SavvyEdu finance REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.edu.finance.schemas import (
    ScholarshipAwardCreate,
    ScholarshipAwardResponse,
    ScholarshipCreate,
    ScholarshipResponse,
    StudentChargeCreate,
    StudentChargeResponse,
    TuitionPlanCreate,
    TuitionPlanResponse,
)
from src.apps.edu.finance.service import EduFinanceService

router = APIRouter(prefix="/finance", tags=["Edu Finance"])


@router.get("/tuition-plans", response_model=list[TuitionPlanResponse])
async def list_tuition_plans(
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduFinanceService.list_tuition_plans(db, org_id)


@router.post("/tuition-plans", response_model=TuitionPlanResponse, status_code=status.HTTP_201_CREATED)
async def create_tuition_plan(
    data: TuitionPlanCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduFinanceService.create_tuition_plan(db, org_id, data)


@router.get("/charges", response_model=list[StudentChargeResponse])
async def list_charges(
    student_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduFinanceService.list_charges(db, org_id, student_id)


@router.post("/charges", response_model=StudentChargeResponse, status_code=status.HTTP_201_CREATED)
async def create_charge(
    data: StudentChargeCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduFinanceService.create_charge(db, org_id, data)


@router.get("/scholarships", response_model=list[ScholarshipResponse])
async def list_scholarships(
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduFinanceService.list_scholarships(db, org_id)


@router.post("/scholarships", response_model=ScholarshipResponse, status_code=status.HTTP_201_CREATED)
async def create_scholarship(
    data: ScholarshipCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduFinanceService.create_scholarship(db, org_id, data)


@router.post("/scholarships/award", response_model=ScholarshipAwardResponse, status_code=status.HTTP_201_CREATED)
async def award_scholarship(
    data: ScholarshipAwardCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduFinanceService.award_scholarship(db, org_id, data)
