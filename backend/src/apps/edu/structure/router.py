"""SavvyEdu academic structure REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.edu.structure.schemas import (
    AcademicPeriodCreate,
    AcademicPeriodResponse,
    AcademicPeriodUpdate,
    CourseCreate,
    CourseResponse,
    CourseUpdate,
    CurriculumVersionCreate,
    CurriculumVersionResponse,
    CurriculumVersionUpdate,
    ProgramCreate,
    ProgramResponse,
    ProgramUpdate,
)
from src.apps.edu.structure.service import AcademicStructureService

router = APIRouter(prefix="/structure", tags=["Edu Structure"])


# ---------------------------------------------------------------------------
# Academic Periods
# ---------------------------------------------------------------------------


@router.get("/periods", response_model=list[AcademicPeriodResponse])
async def list_periods(
    year: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.list_periods(db, org_id, year)


@router.post(
    "/periods",
    response_model=AcademicPeriodResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_period(
    data: AcademicPeriodCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.create_period(db, org_id, data)


@router.get("/periods/{period_id}", response_model=AcademicPeriodResponse)
async def get_period(
    period_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.get_period(db, org_id, period_id)


@router.patch("/periods/{period_id}", response_model=AcademicPeriodResponse)
async def update_period(
    period_id: uuid.UUID,
    data: AcademicPeriodUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.update_period(db, org_id, period_id, data)


# ---------------------------------------------------------------------------
# Programs
# ---------------------------------------------------------------------------


@router.get("/programs", response_model=list[ProgramResponse])
async def list_programs(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.list_programs(db, org_id, status_filter)


@router.post(
    "/programs",
    response_model=ProgramResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_program(
    data: ProgramCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.create_program(db, org_id, data)


@router.get("/programs/{program_id}", response_model=ProgramResponse)
async def get_program(
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.get_program(db, org_id, program_id)


@router.patch("/programs/{program_id}", response_model=ProgramResponse)
async def update_program(
    program_id: uuid.UUID,
    data: ProgramUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.update_program(db, org_id, program_id, data)


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------


@router.get("/courses", response_model=dict)
async def list_courses(
    program_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    items, total = await AcademicStructureService.list_courses(
        db, org_id, program_id, search, page, page_size,
    )
    return {"items": items, "total": total, "page": page, "page_size": page_size}


@router.post(
    "/courses",
    response_model=CourseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_course(
    data: CourseCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.create_course(db, org_id, data)


@router.get("/courses/{course_id}", response_model=CourseResponse)
async def get_course(
    course_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.get_course(db, org_id, course_id)


@router.patch("/courses/{course_id}", response_model=CourseResponse)
async def update_course(
    course_id: uuid.UUID,
    data: CourseUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.update_course(db, org_id, course_id, data)


# ---------------------------------------------------------------------------
# Curriculum Versions
# ---------------------------------------------------------------------------


@router.get("/programs/{program_id}/curriculum", response_model=list[CurriculumVersionResponse])
async def list_curriculum_versions(
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.list_curriculum_versions(db, program_id)


@router.post(
    "/curriculum",
    response_model=CurriculumVersionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_curriculum_version(
    data: CurriculumVersionCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.create_curriculum_version(db, data)


@router.patch("/curriculum/{cv_id}", response_model=CurriculumVersionResponse)
async def update_curriculum_version(
    cv_id: uuid.UUID,
    data: CurriculumVersionUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AcademicStructureService.update_curriculum_version(db, cv_id, data)
