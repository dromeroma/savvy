"""SavvyEdu grading REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.edu.grading.schemas import (
    BulkGradeCreate,
    EvaluationCreate,
    EvaluationResponse,
    EvaluationUpdate,
    FinalGradeResponse,
    GradeResponse,
)
from src.apps.edu.grading.service import GradingService

router = APIRouter(prefix="/grading", tags=["Edu Grading"])


# Evaluations
@router.get("/evaluations", response_model=list[EvaluationResponse])
async def list_evaluations(
    section_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await GradingService.list_evaluations(db, org_id, section_id)


@router.post("/evaluations", response_model=EvaluationResponse, status_code=status.HTTP_201_CREATED)
async def create_evaluation(
    data: EvaluationCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await GradingService.create_evaluation(db, org_id, data)


@router.patch("/evaluations/{eval_id}", response_model=EvaluationResponse)
async def update_evaluation(
    eval_id: uuid.UUID,
    data: EvaluationUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await GradingService.update_evaluation(db, org_id, eval_id, data)


# Grades
@router.post("/grades/bulk", response_model=list[GradeResponse], status_code=status.HTTP_201_CREATED)
async def record_grades(
    data: BulkGradeCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await GradingService.record_grades(db, org_id, data)


@router.get("/grades", response_model=list[GradeResponse])
async def list_grades(
    evaluation_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await GradingService.list_grades(db, org_id, evaluation_id)


# Final Grades
@router.post("/final-grades/{section_id}/calculate", response_model=list[FinalGradeResponse])
async def calculate_final_grades(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await GradingService.calculate_final_grades(db, org_id, section_id)


@router.get("/final-grades/{section_id}", response_model=list[FinalGradeResponse])
async def list_final_grades(
    section_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await GradingService.list_final_grades(db, org_id, section_id)
