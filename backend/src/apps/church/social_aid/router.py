"""Social aid REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.church.social_aid.schemas import (
    AidProgramCreate,
    AidProgramResponse,
    AidProgramUpdate,
    BeneficiaryCreate,
    BeneficiaryResponse,
    BeneficiaryUpdate,
    DistributionCreate,
    DistributionResponse,
)
from src.apps.church.social_aid.service import (
    AidProgramService,
    BeneficiaryService,
    DistributionService,
)

router = APIRouter(
    prefix="/social-aid",
    tags=["Church Social Aid"],
    dependencies=[Depends(require_permission("church", "social_aid.manage"))],
)


# ------------------------------------------------------------------
# Programs
# ------------------------------------------------------------------

@router.get("/programs", response_model=list[AidProgramResponse])
async def list_programs(
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AidProgramService.list_programs(db, org_id, status_filter)


@router.post(
    "/programs",
    response_model=AidProgramResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_program(
    data: AidProgramCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AidProgramService.create_program(db, org_id, data)


@router.get("/programs/{program_id}", response_model=AidProgramResponse)
async def get_program(
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AidProgramService.get_program(db, org_id, program_id)


@router.patch("/programs/{program_id}", response_model=AidProgramResponse)
async def update_program(
    program_id: uuid.UUID,
    data: AidProgramUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AidProgramService.update_program(db, org_id, program_id, data)


# ------------------------------------------------------------------
# Beneficiaries
# ------------------------------------------------------------------

@router.get(
    "/programs/{program_id}/beneficiaries",
    response_model=list[BeneficiaryResponse],
)
async def list_beneficiaries(
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await BeneficiaryService.list_for_program(db, org_id, program_id)


@router.post(
    "/beneficiaries",
    response_model=BeneficiaryResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_beneficiary(
    data: BeneficiaryCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await BeneficiaryService.create_beneficiary(db, org_id, data)


@router.patch(
    "/beneficiaries/{beneficiary_id}",
    response_model=BeneficiaryResponse,
)
async def update_beneficiary(
    beneficiary_id: uuid.UUID,
    data: BeneficiaryUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await BeneficiaryService.update_beneficiary(
        db, org_id, beneficiary_id, data,
    )


# ------------------------------------------------------------------
# Distributions
# ------------------------------------------------------------------

@router.get(
    "/programs/{program_id}/distributions",
    response_model=list[DistributionResponse],
)
async def list_distributions(
    program_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DistributionService.list_for_program(db, org_id, program_id)


@router.post(
    "/distributions",
    response_model=DistributionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_distribution(
    data: DistributionCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DistributionService.create_distribution(db, org_id, data)
