"""Endpoints REST de RRHH."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.hr.schemas import (
    AttendanceCreate,
    AttendanceListItem,
    AttendanceResponse,
    AttendanceUpdate,
    EmployeeCreate,
    EmployeeListItem,
    EmployeeResponse,
    EmployeeUpdate,
    PositionCreate,
    PositionResponse,
    PositionUpdate,
)
from src.apps.memorial.hr.service import (
    AttendanceService,
    EmployeesService,
    PositionsService,
)
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/hr", tags=["Memorial · RRHH"])


def _user_uuid(user: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(user["sub"])


def _perm_read():
    return Depends(require_permission(
        "memorial", "hr.read", "hr.manage",
    ))


def _perm_manage():
    return Depends(require_permission("memorial", "hr.manage"))


# ---------------------------------------------------------------- Positions


@router.get("/positions", response_model=list[PositionResponse], dependencies=[_perm_read()])
async def list_positions(active_only: bool = Query(False), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PositionsService.list_(db, org_id, active_only=active_only)


@router.get("/positions/{pid}", response_model=PositionResponse, dependencies=[_perm_read()])
async def get_position(pid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PositionsService.get(db, org_id, pid)


@router.post("/positions", response_model=PositionResponse, status_code=status.HTTP_201_CREATED, dependencies=[_perm_manage()])
async def create_position(data: PositionCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PositionsService.create(db, org_id, data)


@router.patch("/positions/{pid}", response_model=PositionResponse, dependencies=[_perm_manage()])
async def update_position(pid: uuid.UUID, data: PositionUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await PositionsService.update(db, org_id, pid, data)


@router.delete("/positions/{pid}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, dependencies=[_perm_manage()])
async def delete_position(pid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> None:
    await PositionsService.delete(db, org_id, pid)


# ---------------------------------------------------------------- Employees


@router.get("/employees", response_model=list[EmployeeListItem], dependencies=[_perm_read()])
async def list_employees(
    status_: str | None = Query(None, alias="status"),
    position_id: uuid.UUID | None = Query(None),
    search: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EmployeesService.list_(db, org_id, status=status_, position_id=position_id, search=search)


@router.get("/employees/{eid}", response_model=EmployeeResponse, dependencies=[_perm_read()])
async def get_employee(eid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await EmployeesService.get(db, org_id, eid)


@router.post("/employees", response_model=EmployeeResponse, status_code=status.HTTP_201_CREATED, dependencies=[_perm_manage()])
async def create_employee(data: EmployeeCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await EmployeesService.create(db, org_id, data)


@router.patch("/employees/{eid}", response_model=EmployeeResponse, dependencies=[_perm_manage()])
async def update_employee(eid: uuid.UUID, data: EmployeeUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await EmployeesService.update(db, org_id, eid, data)


@router.delete("/employees/{eid}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, dependencies=[_perm_manage()])
async def delete_employee(eid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> None:
    await EmployeesService.delete(db, org_id, eid)


# ---------------------------------------------------------------- Attendance


@router.get("/attendance", response_model=list[AttendanceListItem], dependencies=[_perm_read()])
async def list_attendance(
    employee_id: uuid.UUID | None = Query(None),
    date_from: str | None = Query(None),
    date_to: str | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AttendanceService.list_(
        db, org_id, employee_id=employee_id,
        date_from=date_from, date_to=date_to, status=status_,
        limit=limit, offset=offset,
    )


@router.post("/attendance", response_model=AttendanceResponse, status_code=status.HTTP_201_CREATED, dependencies=[_perm_manage()])
async def upsert_attendance(
    data: AttendanceCreate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await AttendanceService.upsert(db, org_id, data, _user_uuid(user))


@router.patch("/attendance/{aid}", response_model=AttendanceResponse, dependencies=[_perm_manage()])
async def update_attendance(
    aid: uuid.UUID,
    data: AttendanceUpdate,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await AttendanceService.update(db, org_id, aid, data)


@router.delete("/attendance/{aid}", status_code=status.HTTP_204_NO_CONTENT, response_model=None, dependencies=[_perm_manage()])
async def delete_attendance(aid: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> None:
    await AttendanceService.delete(db, org_id, aid)
