"""Endpoints REST de contratos exequiales + beneficiarios + lookup."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.contracts.schemas import (
    BeneficiaryCreate,
    BeneficiaryResponse,
    BeneficiaryUpdate,
    ContractCreate,
    ContractListItem,
    ContractResponse,
    ContractUpdate,
    CoverageLookupResult,
    TransitionRequest,
)
from src.apps.memorial.contracts.service import ContractsService
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/contracts", tags=["Memorial · Contratos exequiales"])


def _user_uuid(user: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(user["sub"])


def _beneficiary_response(b) -> BeneficiaryResponse:
    return BeneficiaryResponse(
        id=b.id, contract_id=b.contract_id,
        first_name=b.first_name, last_name=b.last_name,
        document_type=b.document_type, document_number=b.document_number,
        birth_date=b.birth_date, gender=b.gender,
        relationship=b.relationship_,
        is_titular=b.is_titular,
        joined_at=b.joined_at,
        removed_at=b.removed_at, removed_reason=b.removed_reason,
        created_at=b.created_at, updated_at=b.updated_at,
    )


async def _hydrate(db: AsyncSession, org_id: uuid.UUID, contract_id: uuid.UUID) -> ContractResponse:
    c, plan, beneficiaries = await ContractsService.get_contract_with_relations(db, org_id, contract_id)
    resp = ContractResponse.model_validate(c)
    resp.plan_name = plan.name if plan else None
    resp.plan_type = plan.plan_type if plan else None
    resp.beneficiaries = [_beneficiary_response(b) for b in beneficiaries]
    return resp


# ---------------------------------------------------------------- List + detail


@router.get(
    "",
    response_model=list[ContractListItem],
    dependencies=[Depends(require_permission("memorial", "contracts.read", "contracts.manage"))],
)
async def list_contracts(
    search: str | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    plan_id: uuid.UUID | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ContractsService.list_contracts(
        db, org_id, search=search, status_=status_,
        plan_id=plan_id, limit=limit, offset=offset,
    )


@router.get(
    "/coverage-lookup",
    response_model=list[CoverageLookupResult],
    dependencies=[Depends(require_permission(
        "memorial", "contracts.read", "contracts.manage", "services.manage",
    ))],
)
async def coverage_lookup(
    document_number: str = Query(..., min_length=1),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ContractsService.coverage_by_document(db, org_id, document_number)


@router.get(
    "/{contract_id}",
    response_model=ContractResponse,
    dependencies=[Depends(require_permission("memorial", "contracts.read", "contracts.manage"))],
)
async def get_contract(
    contract_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await _hydrate(db, org_id, contract_id)


# ---------------------------------------------------------------- Create / update


@router.post(
    "",
    response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "contracts.manage"))],
)
async def create_contract(
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    c = await ContractsService.create_contract(db, org_id, data, _user_uuid(user))
    return await _hydrate(db, org_id, c.id)


@router.patch(
    "/{contract_id}",
    response_model=ContractResponse,
    dependencies=[Depends(require_permission("memorial", "contracts.manage"))],
)
async def update_contract(
    contract_id: uuid.UUID,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    await ContractsService.update_contract(db, org_id, contract_id, data)
    return await _hydrate(db, org_id, contract_id)


@router.post(
    "/{contract_id}/transition",
    response_model=ContractResponse,
    dependencies=[Depends(require_permission("memorial", "contracts.manage"))],
)
async def transition_status(
    contract_id: uuid.UUID,
    req: TransitionRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    await ContractsService.transition_status(db, org_id, contract_id, req)
    return await _hydrate(db, org_id, contract_id)


# ---------------------------------------------------------------- Beneficiaries


@router.post(
    "/{contract_id}/beneficiaries",
    response_model=BeneficiaryResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "contracts.manage"))],
)
async def add_beneficiary(
    contract_id: uuid.UUID,
    data: BeneficiaryCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    b = await ContractsService.add_beneficiary(db, org_id, contract_id, data)
    return _beneficiary_response(b)


@router.patch(
    "/{contract_id}/beneficiaries/{beneficiary_id}",
    response_model=BeneficiaryResponse,
    dependencies=[Depends(require_permission("memorial", "contracts.manage"))],
)
async def update_beneficiary(
    contract_id: uuid.UUID,
    beneficiary_id: uuid.UUID,
    data: BeneficiaryUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    b = await ContractsService.update_beneficiary(
        db, org_id, contract_id, beneficiary_id, data,
    )
    return _beneficiary_response(b)


@router.delete(
    "/{contract_id}/beneficiaries/{beneficiary_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_model=None,
    dependencies=[Depends(require_permission("memorial", "contracts.manage"))],
)
async def remove_beneficiary(
    contract_id: uuid.UUID,
    beneficiary_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await ContractsService.remove_beneficiary(db, org_id, contract_id, beneficiary_id)
