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
from src.apps.hr.service_phase3 import (
    PayrollConceptsService,
    PayrollPeriodsService,
    PayrollsService,
)
from src.apps.hr.service_phase4 import (
    EvaluationCyclesService,
    EvaluationsService,
    ReportsService,
    TrainingCoursesService,
    TrainingEnrollmentsService,
)
from src.apps.hr.schemas import (
    CalculationResult,
    EvaluationCycleCreate,
    EvaluationCycleResponse,
    EvaluationCycleUpdate,
    EvaluationResponseInput,
    EvaluationResponseItem,
    EvaluationResponseSchema,
    EvaluationWithResponses,
    PayrollConceptCreate,
    PayrollConceptResponse,
    PayrollConceptUpdate,
    PayrollListItem,
    PayrollPaymentRequest,
    PayrollPeriodCreate,
    PayrollPeriodResponse,
    PayrollPeriodUpdate,
    PayrollResponse,
    PayrollWithItems,
    ReportAbsenteeismResponse,
    ReportCostResponse,
    ReportHeadcountResponse,
    ReportTenureResponse,
    ReportTrainingSummary,
    TrainingCourseCreate,
    TrainingCourseResponse,
    TrainingCourseUpdate,
    TrainingEnrollmentCreate,
    TrainingEnrollmentResponse,
    TrainingEnrollmentUpdate,
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


def _perm_payroll_run():
    return Depends(require_permission("hr", "hr.payroll.run"))


def _perm_payroll_approve():
    return Depends(require_permission("hr", "hr.payroll.approve"))


def _perm_eval_manage():
    return Depends(require_permission("hr", "hr.evaluations.manage"))


def _perm_eval_respond():
    return Depends(require_permission(
        "hr", "hr.evaluations.respond", "hr.evaluations.manage",
    ))


def _perm_training():
    return Depends(require_permission("hr", "hr.training.manage"))


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


# ============================================================ Fase 3 — Payroll concepts


@router.get("/payroll-concepts", response_model=list[PayrollConceptResponse], dependencies=[_perm_read()])
async def list_concepts(
    active_only: bool = Query(False),
    concept_type: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PayrollConceptsService.list_(
        db, org_id, active_only=active_only, concept_type=concept_type,
    )


@router.get("/payroll-concepts/{cid}", response_model=PayrollConceptResponse, dependencies=[_perm_read()])
async def get_concept(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PayrollConceptsService.get(db, org_id, cid)


@router.post(
    "/payroll-concepts", response_model=PayrollConceptResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_payroll_run()],
)
async def create_concept(
    data: PayrollConceptCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PayrollConceptsService.create(db, org_id, data)


@router.patch("/payroll-concepts/{cid}", response_model=PayrollConceptResponse, dependencies=[_perm_payroll_run()])
async def update_concept(
    cid: uuid.UUID,
    data: PayrollConceptUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PayrollConceptsService.update(db, org_id, cid, data)


@router.delete(
    "/payroll-concepts/{cid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_payroll_run()],
)
async def delete_concept(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await PayrollConceptsService.delete(db, org_id, cid)


@router.post(
    "/payroll-concepts/seed-country",
    dependencies=[_perm_payroll_run()],
)
async def seed_country_template(
    country_code: str = Query("CO", min_length=2, max_length=3),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    created = await PayrollConceptsService.seed_country_template(db, org_id, country_code)
    return {"country_code": country_code.upper(), "created": created}


# ============================================================ Fase 3 — Payroll periods


@router.get("/payroll-periods", response_model=list[PayrollPeriodResponse], dependencies=[_perm_read()])
async def list_periods(
    status_: str | None = Query(None, alias="status"),
    year: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PayrollPeriodsService.list_(db, org_id, status=status_, year=year)


@router.get("/payroll-periods/{pid}", response_model=PayrollPeriodResponse, dependencies=[_perm_read()])
async def get_period(
    pid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PayrollPeriodsService.get(db, org_id, pid)


@router.post(
    "/payroll-periods", response_model=PayrollPeriodResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_payroll_run()],
)
async def create_period(
    data: PayrollPeriodCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await PayrollPeriodsService.create(db, org_id, data, _user_uuid(user))


@router.patch("/payroll-periods/{pid}", response_model=PayrollPeriodResponse, dependencies=[_perm_payroll_run()])
async def update_period(
    pid: uuid.UUID,
    data: PayrollPeriodUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PayrollPeriodsService.update(db, org_id, pid, data)


@router.delete(
    "/payroll-periods/{pid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_payroll_run()],
)
async def delete_period(
    pid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await PayrollPeriodsService.delete(db, org_id, pid)


@router.post(
    "/payroll-periods/{pid}/calculate",
    response_model=CalculationResult, dependencies=[_perm_payroll_run()],
)
async def calculate_period(
    pid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PayrollPeriodsService.calculate(db, org_id, pid)


@router.post(
    "/payroll-periods/{pid}/approve",
    response_model=PayrollPeriodResponse, dependencies=[_perm_payroll_approve()],
)
async def approve_period(
    pid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await PayrollPeriodsService.approve(db, org_id, pid, _user_uuid(user))


@router.post(
    "/payroll-periods/{pid}/pay",
    response_model=PayrollPeriodResponse, dependencies=[_perm_payroll_approve()],
)
async def pay_period(
    pid: uuid.UUID,
    data: PayrollPaymentRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await PayrollPeriodsService.pay(
        db, org_id, pid, _user_uuid(user),
        payment_reference=data.payment_reference,
        create_finance_transaction=data.create_finance_transaction,
    )


@router.post(
    "/payroll-periods/{pid}/close",
    response_model=PayrollPeriodResponse, dependencies=[_perm_payroll_approve()],
)
async def close_period(
    pid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PayrollPeriodsService.close(db, org_id, pid)


# ============================================================ Fase 3 — Payrolls (read)


@router.get("/payroll-periods/{pid}/payrolls", response_model=list[PayrollResponse], dependencies=[_perm_read()])
async def list_payrolls(
    pid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await PayrollsService.list_by_period(db, org_id, pid)


@router.get("/payrolls/{rid}", response_model=PayrollWithItems, dependencies=[_perm_read()])
async def get_payroll(
    rid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    p = await PayrollsService.get(db, org_id, rid)
    items = await PayrollsService.get_items(db, p.id)
    return {
        **{c.name: getattr(p, c.name) for c in p.__table__.columns},
        "items": items,
    }


@router.get("/payrolls/{rid}/pdf", dependencies=[_perm_read()])
async def get_payroll_pdf(
    rid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    from fastapi.responses import Response
    from src.apps.hr.payroll_pdf import render_payroll_pdf
    p = await PayrollsService.get(db, org_id, rid)
    items = await PayrollsService.get_items(db, p.id)
    period = await PayrollPeriodsService.get(db, org_id, p.period_id)
    pdf_bytes, filename = await render_payroll_pdf(db, org_id, p, items, period)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ============================================================ Fase 4 — Evaluation cycles


@router.get("/evaluation-cycles", response_model=list[EvaluationCycleResponse], dependencies=[_perm_read()])
async def list_evaluation_cycles(
    status_: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EvaluationCyclesService.list_(db, org_id, status=status_)


@router.get("/evaluation-cycles/{cid}", response_model=EvaluationCycleResponse, dependencies=[_perm_read()])
async def get_evaluation_cycle(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EvaluationCyclesService.get(db, org_id, cid)


@router.post(
    "/evaluation-cycles", response_model=EvaluationCycleResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_eval_manage()],
)
async def create_evaluation_cycle(
    data: EvaluationCycleCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await EvaluationCyclesService.create(db, org_id, data, _user_uuid(user))


@router.patch("/evaluation-cycles/{cid}", response_model=EvaluationCycleResponse, dependencies=[_perm_eval_manage()])
async def update_evaluation_cycle(
    cid: uuid.UUID,
    data: EvaluationCycleUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EvaluationCyclesService.update(db, org_id, cid, data)


@router.delete(
    "/evaluation-cycles/{cid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_eval_manage()],
)
async def delete_evaluation_cycle(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await EvaluationCyclesService.delete(db, org_id, cid)


@router.post(
    "/evaluation-cycles/{cid}/open", dependencies=[_perm_eval_manage()],
)
async def open_evaluation_cycle(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EvaluationCyclesService.open_cycle(db, org_id, cid)


@router.post(
    "/evaluation-cycles/{cid}/close",
    response_model=EvaluationCycleResponse, dependencies=[_perm_eval_manage()],
)
async def close_evaluation_cycle(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EvaluationCyclesService.close_cycle(db, org_id, cid)


# ============================================================ Fase 4 — Evaluations


@router.get(
    "/evaluation-cycles/{cid}/evaluations",
    response_model=list[EvaluationResponseSchema], dependencies=[_perm_read()],
)
async def list_evaluations_by_cycle(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EvaluationsService.list_by_cycle(db, org_id, cid)


@router.get("/evaluations/{eid}", response_model=EvaluationWithResponses, dependencies=[_perm_read()])
async def get_evaluation_detail(
    eid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    e = await EvaluationsService.get(db, org_id, eid)
    responses = await EvaluationsService.get_responses(db, e.id)
    return {
        **{c.name: getattr(e, c.name) for c in e.__table__.columns},
        "responses": responses,
    }


@router.post(
    "/evaluations/{eid}/responses",
    response_model=EvaluationResponseItem,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_eval_respond()],
)
async def submit_evaluation_response(
    eid: uuid.UUID,
    data: EvaluationResponseInput,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await EvaluationsService.submit_response(db, org_id, eid, data, _user_uuid(user))


# ============================================================ Fase 4 — Training courses


@router.get("/training-courses", response_model=list[TrainingCourseResponse], dependencies=[_perm_read()])
async def list_training_courses(
    active_only: bool = Query(False),
    category: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TrainingCoursesService.list_(db, org_id, active_only=active_only, category=category)


@router.get("/training-courses/{cid}", response_model=TrainingCourseResponse, dependencies=[_perm_read()])
async def get_training_course(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TrainingCoursesService.get(db, org_id, cid)


@router.post(
    "/training-courses", response_model=TrainingCourseResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_training()],
)
async def create_training_course(
    data: TrainingCourseCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TrainingCoursesService.create(db, org_id, data)


@router.patch("/training-courses/{cid}", response_model=TrainingCourseResponse, dependencies=[_perm_training()])
async def update_training_course(
    cid: uuid.UUID,
    data: TrainingCourseUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TrainingCoursesService.update(db, org_id, cid, data)


@router.delete(
    "/training-courses/{cid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_training()],
)
async def delete_training_course(
    cid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await TrainingCoursesService.delete(db, org_id, cid)


# ============================================================ Fase 4 — Training enrollments


@router.get("/training-enrollments", response_model=list[TrainingEnrollmentResponse], dependencies=[_perm_read()])
async def list_training_enrollments(
    course_id: uuid.UUID | None = Query(None),
    employee_id: uuid.UUID | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TrainingEnrollmentsService.list_(
        db, org_id, course_id=course_id, employee_id=employee_id, status=status_,
    )


@router.post(
    "/training-enrollments", response_model=TrainingEnrollmentResponse,
    status_code=status.HTTP_201_CREATED, dependencies=[_perm_training()],
)
async def create_training_enrollment(
    data: TrainingEnrollmentCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await TrainingEnrollmentsService.create(db, org_id, data, _user_uuid(user))


@router.patch("/training-enrollments/{eid}", response_model=TrainingEnrollmentResponse, dependencies=[_perm_training()])
async def update_training_enrollment(
    eid: uuid.UUID,
    data: TrainingEnrollmentUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await TrainingEnrollmentsService.update(db, org_id, eid, data)


@router.delete(
    "/training-enrollments/{eid}", status_code=status.HTTP_204_NO_CONTENT,
    response_model=None, dependencies=[_perm_training()],
)
async def delete_training_enrollment(
    eid: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> None:
    await TrainingEnrollmentsService.delete(db, org_id, eid)


# ============================================================ Fase 4 — Reports


@router.get("/reports/headcount-by-department", response_model=ReportHeadcountResponse, dependencies=[_perm_read()])
async def report_headcount_by_department(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReportsService.headcount_by_department(db, org_id)


@router.get("/reports/tenure-distribution", response_model=ReportTenureResponse, dependencies=[_perm_read()])
async def report_tenure_distribution(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReportsService.tenure_distribution(db, org_id)


@router.get(
    "/reports/cost-by-department/{period_id}",
    response_model=ReportCostResponse, dependencies=[_perm_read()],
)
async def report_cost_by_department(
    period_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReportsService.cost_by_department(db, org_id, period_id)


@router.get("/reports/absenteeism", response_model=ReportAbsenteeismResponse, dependencies=[_perm_read()])
async def report_absenteeism(
    date_from: _date = Query(...),
    date_to: _date = Query(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReportsService.absenteeism(db, org_id, date_from, date_to)


@router.get("/reports/training-summary", response_model=list[ReportTrainingSummary], dependencies=[_perm_read()])
async def report_training_summary(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ReportsService.training_summary(db, org_id)


# ============================================================ Fase 5: Settings + Liquidación

from fastapi import Response  # noqa: E402
from src.apps.hr.liquidation_pdf import render_liquidation_pdf, render_liquidation_preview_pdf  # noqa: E402
from src.apps.hr.service_phase5 import HrSettingsService, LiquidationsService  # noqa: E402
from src.apps.hr.schemas import (  # noqa: E402
    HrSettingsResponse,
    HrSettingsUpdate,
    LiquidationCalculationInput,
    LiquidationCalculationPreview,
    LiquidationCreate,
    LiquidationDetail,
    LiquidationItemEdit,
    LiquidationItemSchema,
    LiquidationListItem,
    LiquidationResponse,
)


def _perm_payroll_or_emp():
    return Depends(require_permission(
        "hr", "hr.payroll.run", "hr.employees.manage",
    ))


# ---------- HR Settings ----------

@router.get("/settings", response_model=HrSettingsResponse, dependencies=[_perm_read()])
async def get_hr_settings(
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await HrSettingsService.get_or_create(db, org_id)


@router.patch("/settings", response_model=HrSettingsResponse, dependencies=[_perm_emp_manage()])
async def update_hr_settings(
    data: HrSettingsUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await HrSettingsService.update(db, org_id, data)


@router.get("/settings/preview-pdf", dependencies=[_perm_read()])
async def liquidation_preview_pdf(
    template: str = Query("formal", description="formal | moderna | compacta"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Response:
    """PDF de muestra con datos de prueba para previsualizar la plantilla."""
    pdf_bytes, filename = await render_liquidation_preview_pdf(db, org_id, template)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ---------- Liquidations ----------

def _liq_detail(liq, items, emp, dept_name, pos_name) -> dict[str, Any]:
    full = " ".join(x for x in [emp.first_name, emp.last_name] if x).strip()
    return {
        **{c.name: getattr(liq, c.name) for c in liq.__table__.columns},
        "employee_code": emp.employee_code,
        "employee_name": full,
        "department_name": dept_name,
        "position_name": pos_name,
        "items": [
            {
                "id": it.id, "concept_code": it.concept_code, "concept_name": it.concept_name,
                "kind": it.kind, "quantity": it.quantity, "base_amount": it.base_amount,
                "rate": it.rate, "amount": it.amount, "is_manual": it.is_manual,
                "sort_order": it.sort_order, "notes": it.notes,
            } for it in items
        ],
    }


@router.post("/liquidations/calculate", response_model=LiquidationCalculationPreview, dependencies=[_perm_payroll_or_emp()])
async def calculate_liquidation_preview(
    data: LiquidationCalculationInput,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    result = await LiquidationsService.calculate(db, org_id, data)
    return {
        "base_salary": result.base_salary,
        "average_salary": result.average_salary,
        "days_worked_total": result.days_worked_total,
        "contract_start_date": result.contract_start_date,
        "last_worked_date": result.last_worked_date,
        "termination_date": result.termination_date,
        "termination_reason": result.termination_reason,
        "total_earnings": result.total_earnings,
        "total_deductions": result.total_deductions,
        "net_amount": result.net_amount,
        "items": [
            {
                "concept_code": it.code, "concept_name": it.name, "kind": it.kind,
                "quantity": it.quantity, "base_amount": it.base_amount,
                "rate": it.rate, "amount": it.amount, "is_manual": False,
                "sort_order": it.sort_order, "notes": it.notes,
            } for it in result.items
        ],
    }


@router.get("/liquidations", response_model=list[LiquidationListItem], dependencies=[_perm_read()])
async def list_liquidations(
    status: str | None = Query(None),
    employee_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    rows = await LiquidationsService.list_(db, org_id, status=status, employee_id=employee_id)
    return [
        {
            "id": liq.id, "liquidation_number": liq.liquidation_number,
            "employee_id": emp.id, "employee_code": emp.employee_code,
            "employee_name": " ".join(x for x in [emp.first_name, emp.last_name] if x).strip(),
            "termination_date": liq.termination_date,
            "termination_reason": liq.termination_reason,
            "net_amount": liq.net_amount, "currency": liq.currency,
            "status": liq.status, "created_at": liq.created_at,
        }
        for liq, emp in rows
    ]


@router.post("/liquidations", response_model=LiquidationResponse, status_code=status.HTTP_201_CREATED, dependencies=[_perm_payroll_or_emp()])
async def create_liquidation(
    data: LiquidationCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await LiquidationsService.create(db, org_id, data, created_by=_user_uuid(user))


@router.get("/liquidations/{liq_id}", response_model=LiquidationDetail, dependencies=[_perm_read()])
async def get_liquidation(
    liq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    from src.apps.hr.models import HrEmployee, HrDepartment, HrPosition
    from sqlalchemy import select as _select
    liq = await LiquidationsService.get(db, org_id, liq_id)
    items = await LiquidationsService.get_items(db, liq_id)
    emp = (await db.execute(_select(HrEmployee).where(HrEmployee.id == liq.employee_id))).scalar_one()
    dept_name = None
    pos_name = None
    if emp.department_id:
        d = (await db.execute(_select(HrDepartment).where(HrDepartment.id == emp.department_id))).scalar_one_or_none()
        dept_name = d.name if d else None
    if emp.position_id:
        p = (await db.execute(_select(HrPosition).where(HrPosition.id == emp.position_id))).scalar_one_or_none()
        pos_name = p.name if p else None
    return _liq_detail(liq, items, emp, dept_name, pos_name)


@router.patch("/liquidations/{liq_id}", response_model=LiquidationResponse, dependencies=[_perm_payroll_or_emp()])
async def edit_liquidation_items(
    liq_id: uuid.UUID,
    data: LiquidationItemEdit,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LiquidationsService.edit_items(db, org_id, liq_id, data)


@router.post("/liquidations/{liq_id}/finalize", response_model=LiquidationResponse, dependencies=[_perm_payroll_or_emp()])
async def finalize_liquidation(
    liq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await LiquidationsService.finalize(db, org_id, liq_id, finalized_by=_user_uuid(user))


@router.post("/liquidations/{liq_id}/mark-paid", response_model=LiquidationResponse, dependencies=[_perm_payroll_or_emp()])
async def mark_liquidation_paid(
    liq_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await LiquidationsService.mark_paid(db, org_id, liq_id)


@router.get("/liquidations/{liq_id}/pdf", dependencies=[_perm_read()])
async def liquidation_pdf(
    liq_id: uuid.UUID,
    template: str | None = Query(None, description="formal | moderna | compacta"),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Response:
    liq = await LiquidationsService.get(db, org_id, liq_id)
    items = await LiquidationsService.get_items(db, liq_id)
    pdf_bytes, filename = await render_liquidation_pdf(
        db, org_id, liq, items, template_key=template,
    )
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
