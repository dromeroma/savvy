"""Endpoints REST de SavvyHR fase 1."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hr.schemas import (
    AttendanceCreate,
    AttendanceListItem,
    AttendanceResponse,
    AttendanceUpdate,
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
    LeaveCreate,
    LeaveResponse,
    LeaveUpdate,
    PositionCreate,
    PositionResponse,
    PositionUpdate,
    ShiftCreate,
    ShiftResponse,
    ShiftUpdate,
    VacationApproval,
    VacationBalanceAdjust,
    VacationBalanceResponse,
    VacationRejection,
    VacationRequestCreate,
    VacationRequestResponse,
)
from src.apps.hr.service import (
    ContractsService,
    DepartmentsService,
    DocumentsService,
    EmployeesService,
    PositionsService,
)
from src.apps.hr.service_phase2 import (
    AttendanceService,
    LeavesService,
    ShiftsService,
    VacationBalancesService,
    VacationRequestsService,
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


def _perm_attendance():
    return Depends(require_permission("hr", "hr.attendance.manage"))


def _perm_vacations():
    return Depends(require_permission("hr", "hr.vacations.manage"))


def _perm_vacations_approve():
    return Depends(require_permission("hr", "hr.vacations.approve"))


def _perm_leaves():
    return Depends(require_permission("hr", "hr.leaves.manage"))


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


# ============================================================ Fase 2 — Shifts


from datetime import date as _date  # noqa: E402


@router.get("/shifts", response_model=list[ShiftResponse], dependencies=[_perm_read()])
async def list_shifts(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ShiftsService.list_(db, org_id, active_only=active_only)


@router.get("/shifts/{sid}", response_model=ShiftResponse, dependencies=[_perm_read()])
async def get_shift(
    sid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ShiftsService.get(db, org_id, sid)


@router.post(
    "/shifts", response_model=ShiftResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_attendance()],
)
async def create_shift(
    data: ShiftCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ShiftsService.create(db, org_id, data)


@router.patch("/shifts/{sid}", response_model=ShiftResponse, dependencies=[_perm_attendance()])
async def update_shift(
    sid: uuid.UUID,
    data: ShiftUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ShiftsService.update(db, org_id, sid, data)


@router.delete(
    "/shifts/{sid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_attendance()],
)
async def delete_shift(
    sid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await ShiftsService.delete(db, org_id, sid)


# ============================================================ Fase 2 — Attendance


@router.get("/attendance", response_model=list[AttendanceListItem], dependencies=[_perm_read()])
async def list_attendance(
    employee_id: uuid.UUID | None = Query(None),
    date_from: _date | None = Query(None),
    date_to: _date | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AttendanceService.list_(
        db, org_id,
        employee_id=employee_id, date_from=date_from, date_to=date_to,
        status=status_, limit=limit, offset=offset,
    )


@router.post(
    "/attendance", response_model=AttendanceResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_attendance()],
)
async def upsert_attendance(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await AttendanceService.upsert(db, org_id, data, _user_uuid(user))


@router.patch("/attendance/{aid}", response_model=AttendanceResponse, dependencies=[_perm_attendance()])
async def update_attendance(
    aid: uuid.UUID,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AttendanceService.update(db, org_id, aid, data)


@router.delete(
    "/attendance/{aid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_attendance()],
)
async def delete_attendance(
    aid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await AttendanceService.delete(db, org_id, aid)


# ============================================================ Fase 2 — Vacation balances


@router.get("/vacation-balances", response_model=list[VacationBalanceResponse], dependencies=[_perm_read()])
async def list_vacation_balances(
    period_year: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await VacationBalancesService.list_org(db, org_id, period_year=period_year)


@router.get(
    "/employees/{eid}/vacation-balances",
    response_model=list[VacationBalanceResponse], dependencies=[_perm_read()],
)
async def employee_vacation_balances(
    eid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await VacationBalancesService.list_for_employee(db, org_id, eid)


@router.post(
    "/employees/{eid}/vacation-balances/adjust",
    response_model=VacationBalanceResponse, dependencies=[_perm_vacations()],
)
async def adjust_vacation_balance(
    eid: uuid.UUID,
    data: VacationBalanceAdjust,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await VacationBalancesService.adjust(db, org_id, eid, data)


@router.post(
    "/vacation-balances/accrue", dependencies=[_perm_vacations()],
)
async def run_monthly_accrual(
    days_per_month: float = Query(1.25, ge=0, le=10),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    from decimal import Decimal as _D
    count = await VacationBalancesService.accrue_monthly(
        db, org_id, days_per_month=_D(str(days_per_month)),
    )
    return {"accrued_employees": count}


# ============================================================ Fase 2 — Vacation requests


@router.get("/vacation-requests", response_model=list[VacationRequestResponse], dependencies=[_perm_read()])
async def list_vacation_requests(
    employee_id: uuid.UUID | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await VacationRequestsService.list_(db, org_id, employee_id=employee_id, status=status_)


@router.get("/vacation-requests/{rid}", response_model=VacationRequestResponse, dependencies=[_perm_read()])
async def get_vacation_request(
    rid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await VacationRequestsService.get(db, org_id, rid)


@router.post(
    "/vacation-requests", response_model=VacationRequestResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_vacations()],
)
async def create_vacation_request(
    data: VacationRequestCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await VacationRequestsService.create(db, org_id, data, _user_uuid(user))


@router.post(
    "/vacation-requests/{rid}/approve",
    response_model=VacationRequestResponse, dependencies=[_perm_vacations_approve()],
)
async def approve_vacation(
    rid: uuid.UUID,
    data: VacationApproval,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await VacationRequestsService.approve(db, org_id, rid, data.notes, _user_uuid(user))


@router.post(
    "/vacation-requests/{rid}/reject",
    response_model=VacationRequestResponse, dependencies=[_perm_vacations_approve()],
)
async def reject_vacation(
    rid: uuid.UUID,
    data: VacationRejection,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await VacationRequestsService.reject(db, org_id, rid, data.rejection_reason, _user_uuid(user))


@router.post(
    "/vacation-requests/{rid}/cancel",
    response_model=VacationRequestResponse, dependencies=[_perm_vacations()],
)
async def cancel_vacation(
    rid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await VacationRequestsService.cancel(db, org_id, rid)


# ============================================================ Fase 2 — Leaves


@router.get("/leaves", response_model=list[LeaveResponse], dependencies=[_perm_read()])
async def list_leaves(
    employee_id: uuid.UUID | None = Query(None),
    leave_type: str | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LeavesService.list_(
        db, org_id, employee_id=employee_id, leave_type=leave_type, status=status_,
    )


@router.get("/leaves/{lid}", response_model=LeaveResponse, dependencies=[_perm_read()])
async def get_leave(
    lid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LeavesService.get(db, org_id, lid)


@router.post(
    "/leaves", response_model=LeaveResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_leaves()],
)
async def create_leave(
    data: LeaveCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await LeavesService.create(db, org_id, data, _user_uuid(user))


@router.patch("/leaves/{lid}", response_model=LeaveResponse, dependencies=[_perm_leaves()])
async def update_leave(
    lid: uuid.UUID,
    data: LeaveUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LeavesService.update(db, org_id, lid, data)


@router.delete(
    "/leaves/{lid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_leaves()],
)
async def delete_leave(
    lid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await LeavesService.delete(db, org_id, lid)
