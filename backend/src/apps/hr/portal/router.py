"""Portal HR · endpoints públicos (autenticados con JWT scope:hr_portal)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hr.payroll_pdf import render_payroll_pdf
from src.apps.hr.portal.schemas import (
    PortalAuthRequest,
    PortalAuthResponse,
    PortalContractItem,
    PortalDocumentItem,
    PortalEmployee,
    PortalEvaluationDetail,
    PortalEvaluationItem,
    PortalEvaluationResponseInput,
    PortalLeaveItem,
    PortalPayrollItem,
    PortalTrainingItem,
    PortalVacationBalance,
    PortalVacationRequest,
    PortalVacationRequestCreate,
)
from src.apps.hr.portal.service import (
    authenticate_portal,
    create_portal_vacation_request,
    decode_portal_token,
    get_portal_employee,
    get_portal_evaluation_detail,
    get_portal_payroll,
    list_portal_contracts,
    list_portal_documents,
    list_portal_evaluations,
    list_portal_leaves,
    list_portal_payrolls,
    list_portal_trainings,
    list_portal_vacation_balances,
    list_portal_vacation_requests,
    submit_portal_evaluation_response,
)
from src.apps.hr.service_phase3 import PayrollPeriodsService, PayrollsService
from src.core.dependencies import get_db
from src.core.exceptions import UnauthorizedError

router = APIRouter(prefix="/hr-portal", tags=["SavvyHR · Portal del empleado"])
bearer = HTTPBearer(auto_error=False)


async def _portal_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, Any]:
    if credentials is None:
        raise UnauthorizedError("Token de portal requerido.")
    return decode_portal_token(credentials.credentials)


def _portal_ctx(payload: dict[str, Any]) -> tuple[uuid.UUID, uuid.UUID]:
    return uuid.UUID(payload["employee_id"]), uuid.UUID(payload["org_id"])


# ============================================================ Auth


@router.post("/auth", response_model=PortalAuthResponse)
async def portal_auth(
    data: PortalAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> PortalAuthResponse:
    token, ttl, employee = await authenticate_portal(db, data)
    return PortalAuthResponse(token=token, expires_in_seconds=ttl, employee=employee)


# ============================================================ Me / contracts


@router.get("/me", response_model=PortalEmployee)
async def portal_me(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> PortalEmployee:
    employee_id, org_id = _portal_ctx(payload)
    return await get_portal_employee(db, employee_id, org_id)


@router.get("/contracts", response_model=list[PortalContractItem])
async def portal_contracts(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    return await list_portal_contracts(db, employee_id, org_id)


# ============================================================ Payrolls + PDF


@router.get("/payrolls", response_model=list[PortalPayrollItem])
async def portal_payrolls(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    return await list_portal_payrolls(db, employee_id, org_id)


@router.get("/payrolls/{payroll_id}/pdf")
async def portal_payroll_pdf(
    payroll_id: uuid.UUID,
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Response:
    employee_id, org_id = _portal_ctx(payload)
    p = await get_portal_payroll(db, employee_id, org_id, payroll_id)
    items = await PayrollsService.get_items(db, p.id)
    period = await PayrollPeriodsService.get(db, org_id, p.period_id)
    pdf_bytes, filename = await render_payroll_pdf(db, org_id, p, items, period)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )


# ============================================================ Vacations


@router.get("/vacation-balances", response_model=list[PortalVacationBalance])
async def portal_vacation_balances(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    return await list_portal_vacation_balances(db, employee_id, org_id)


@router.get("/vacation-requests", response_model=list[PortalVacationRequest])
async def portal_vacation_requests(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    return await list_portal_vacation_requests(db, employee_id, org_id)


@router.post("/vacation-requests", response_model=PortalVacationRequest, status_code=201)
async def portal_create_vacation_request(
    data: PortalVacationRequestCreate,
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    return await create_portal_vacation_request(db, employee_id, org_id, data)


# ============================================================ Leaves


@router.get("/leaves", response_model=list[PortalLeaveItem])
async def portal_leaves(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    return await list_portal_leaves(db, employee_id, org_id)


# ============================================================ Evaluations


@router.get("/evaluations", response_model=list[PortalEvaluationItem])
async def portal_evaluations(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    return await list_portal_evaluations(db, employee_id, org_id)


@router.get("/evaluations/{eid}", response_model=PortalEvaluationDetail)
async def portal_evaluation_detail(
    eid: uuid.UUID,
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    return await get_portal_evaluation_detail(db, employee_id, org_id, eid)


@router.post("/evaluations/{eid}/responses", status_code=201)
async def portal_submit_evaluation_response(
    eid: uuid.UUID,
    data: PortalEvaluationResponseInput,
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    r = await submit_portal_evaluation_response(db, employee_id, org_id, eid, data)
    return {"id": r.id, "evaluator_type": r.evaluator_type, "overall_score": r.overall_score}


# ============================================================ Training


@router.get("/trainings", response_model=list[PortalTrainingItem])
async def portal_trainings(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    return await list_portal_trainings(db, employee_id, org_id)


# ============================================================ Documents


@router.get("/documents", response_model=list[PortalDocumentItem])
async def portal_documents(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    employee_id, org_id = _portal_ctx(payload)
    return await list_portal_documents(db, employee_id, org_id)
