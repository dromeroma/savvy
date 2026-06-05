"""Endpoints REST de SavvyHR fase 1."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hr.schemas import (
    ContractCreate,
    ContractResponse,
    ContractUpdate,
    DepartmentCreate,
    DepartmentResponse,
    DepartmentUpdate,
    DocumentCreate,
    DocumentResponse,
    DocumentUpdate,
    EmployeeCreate,
    EmployeeListItem,
    EmployeeResponse,
    EmployeeUpdate,
    PositionCreate,
    PositionResponse,
    PositionUpdate,
)
from src.apps.hr.service import (
    ContractsService,
    DepartmentsService,
    DocumentsService,
    EmployeesService,
    PositionsService,
)
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/hr", tags=["SavvyHR"])


def _user_uuid(user: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(user["sub"])


def _perm_read():
    return Depends(require_permission(
        "hr", "hr.read", "hr.employees.manage", "hr.contracts.manage",
    ))


def _perm_emp_manage():
    return Depends(require_permission("hr", "hr.employees.manage"))


def _perm_contract_manage():
    return Depends(require_permission("hr", "hr.contracts.manage"))


# ============================================================ Departments


@router.get("/departments", response_model=list[DepartmentResponse], dependencies=[_perm_read()])
async def list_departments(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DepartmentsService.list_(db, org_id, active_only=active_only)


@router.get("/departments/{did}", response_model=DepartmentResponse, dependencies=[_perm_read()])
async def get_department(
    did: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DepartmentsService.get(db, org_id, did)


@router.post(
    "/departments", response_model=DepartmentResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_emp_manage()],
)
async def create_department(
    data: DepartmentCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DepartmentsService.create(db, org_id, data)


@router.patch("/departments/{did}", response_model=DepartmentResponse, dependencies=[_perm_emp_manage()])
async def update_department(
    did: uuid.UUID,
    data: DepartmentUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DepartmentsService.update(db, org_id, did, data)


@router.delete(
    "/departments/{did}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_emp_manage()],
)
async def delete_department(
    did: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await DepartmentsService.delete(db, org_id, did)


# ============================================================ Positions


@router.get("/positions", response_model=list[PositionResponse], dependencies=[_perm_read()])
async def list_positions(
    active_only: bool = Query(False),
    department_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PositionsService.list_(db, org_id, active_only=active_only, department_id=department_id)


@router.get("/positions/{pid}", response_model=PositionResponse, dependencies=[_perm_read()])
async def get_position(
    pid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PositionsService.get(db, org_id, pid)


@router.post(
    "/positions", response_model=PositionResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_emp_manage()],
)
async def create_position(
    data: PositionCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PositionsService.create(db, org_id, data)


@router.patch("/positions/{pid}", response_model=PositionResponse, dependencies=[_perm_emp_manage()])
async def update_position(
    pid: uuid.UUID,
    data: PositionUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PositionsService.update(db, org_id, pid, data)


@router.delete(
    "/positions/{pid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_emp_manage()],
)
async def delete_position(
    pid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await PositionsService.delete(db, org_id, pid)


# ============================================================ Employees


@router.get("/employees", response_model=list[EmployeeListItem], dependencies=[_perm_read()])
async def list_employees(
    status_: str | None = Query(None, alias="status"),
    department_id: uuid.UUID | None = Query(None),
    position_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EmployeesService.list_(
        db, org_id,
        status=status_, department_id=department_id, position_id=position_id, search=search,
    )


@router.get("/employees/{eid}", response_model=EmployeeResponse, dependencies=[_perm_read()])
async def get_employee(
    eid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EmployeesService.get(db, org_id, eid)


@router.post(
    "/employees", response_model=EmployeeResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_emp_manage()],
)
async def create_employee(
    data: EmployeeCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await EmployeesService.create(db, org_id, data, _user_uuid(user))


@router.patch("/employees/{eid}", response_model=EmployeeResponse, dependencies=[_perm_emp_manage()])
async def update_employee(
    eid: uuid.UUID,
    data: EmployeeUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EmployeesService.update(db, org_id, eid, data)


@router.delete(
    "/employees/{eid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_emp_manage()],
)
async def delete_employee(
    eid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await EmployeesService.delete(db, org_id, eid)


# ============================================================ Contracts


@router.get("/contracts", response_model=list[ContractResponse], dependencies=[_perm_read()])
async def list_contracts(
    employee_id: uuid.UUID | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ContractsService.list_(db, org_id, employee_id=employee_id, status=status_)


@router.get("/contracts/{cid}", response_model=ContractResponse, dependencies=[_perm_read()])
async def get_contract(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ContractsService.get(db, org_id, cid)


@router.post(
    "/contracts", response_model=ContractResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_contract_manage()],
)
async def create_contract(
    data: ContractCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await ContractsService.create(db, org_id, data, _user_uuid(user))


@router.patch("/contracts/{cid}", response_model=ContractResponse, dependencies=[_perm_contract_manage()])
async def update_contract(
    cid: uuid.UUID,
    data: ContractUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ContractsService.update(db, org_id, cid, data)


@router.delete(
    "/contracts/{cid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_contract_manage()],
)
async def delete_contract(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await ContractsService.delete(db, org_id, cid)


# ============================================================ Documents


@router.get("/documents", response_model=list[DocumentResponse], dependencies=[_perm_read()])
async def list_documents(
    employee_id: uuid.UUID | None = Query(None),
    document_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DocumentsService.list_(db, org_id, employee_id=employee_id, document_type=document_type)


@router.get("/documents/{did}", response_model=DocumentResponse, dependencies=[_perm_read()])
async def get_document(
    did: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DocumentsService.get(db, org_id, did)


@router.post(
    "/documents", response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_emp_manage()],
)
async def create_document(
    data: DocumentCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await DocumentsService.create(db, org_id, data, _user_uuid(user))


@router.patch("/documents/{did}", response_model=DocumentResponse, dependencies=[_perm_emp_manage()])
async def update_document(
    did: uuid.UUID,
    data: DocumentUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await DocumentsService.update(db, org_id, did, data)


@router.delete(
    "/documents/{did}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_emp_manage()],
)
async def delete_document(
    did: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await DocumentsService.delete(db, org_id, did)
