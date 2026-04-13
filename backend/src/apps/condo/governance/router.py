"""Condo governance REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission
from src.apps.condo.governance.schemas import AssemblyCreate, AssemblyResponse, VoteCreate, VoteResponse
from src.apps.condo.governance.service import GovernanceService

router = APIRouter(
    prefix="/governance",
    tags=["Condo Governance"],
    dependencies=[Depends(require_permission("condo", "governance.manage", "reports.view"))],
)
_WRITE = [Depends(require_permission("condo", "governance.manage"))]


@router.get("/assemblies", response_model=list[AssemblyResponse])
async def list_assemblies(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await GovernanceService.list_assemblies(db, org_id)

@router.post("/assemblies", response_model=AssemblyResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def create_assembly(data: AssemblyCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await GovernanceService.create_assembly(db, org_id, data)

@router.post("/votes", response_model=VoteResponse, status_code=status.HTTP_201_CREATED, dependencies=_WRITE)
async def cast_vote(data: VoteCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await GovernanceService.cast_vote(db, org_id, data)

@router.get("/assemblies/{assembly_id}/votes", response_model=list[VoteResponse])
async def get_votes(assembly_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await GovernanceService.get_vote_results(db, assembly_id)
