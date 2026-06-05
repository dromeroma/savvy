"""Portal HR · lógica de auth + carga de datos del empleado."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hr.models import (
    HrContract,
    HrDepartment,
    HrEmployee,
    HrEmployeeDocument,
    HrEvaluation,
    HrEvaluationCycle,
    HrEvaluationResponse,
    HrLeave,
    HrPayroll,
    HrPayrollPeriod,
    HrPosition,
    HrTrainingCourse,
    HrTrainingEnrollment,
    HrVacationBalance,
    HrVacationRequest,
)
from src.apps.hr.portal.schemas import (
    PortalAuthRequest,
    PortalCompetency,
    PortalEmployee,
    PortalEvaluationDetail,
    PortalEvaluationResponseInput,
    PortalVacationRequestCreate,
)
from src.core.config import get_settings
from src.core.exceptions import (
    ConflictError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from src.modules.organization.models import Organization

settings = get_settings()

PORTAL_TOKEN_TTL_HOURS = 12
PORTAL_TOKEN_SCOPE = "hr_portal"


def issue_portal_token(employee_id: uuid.UUID, org_id: uuid.UUID) -> tuple[str, int]:
    ttl = timedelta(hours=PORTAL_TOKEN_TTL_HOURS)
    expire = datetime.now(UTC) + ttl
    payload = {
        "scope": PORTAL_TOKEN_SCOPE,
        "employee_id": str(employee_id),
        "org_id": str(org_id),
        "exp": expire,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    return token, int(ttl.total_seconds())


def decode_portal_token(token: str) -> dict[str, Any]:
    try:
        payload = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM],
        )
    except JWTError as exc:
        raise UnauthorizedError("Token de portal HR inválido o expirado.") from exc
    if payload.get("scope") != PORTAL_TOKEN_SCOPE:
        raise UnauthorizedError("Token con alcance inválido para portal HR.")
    return payload


async def authenticate_portal(
    db: AsyncSession, data: PortalAuthRequest,
) -> tuple[str, int, PortalEmployee]:
    org = await db.scalar(select(Organization).where(Organization.slug == data.org_slug))
    if org is None:
        raise UnauthorizedError("Organización no encontrada.")

    emp = await db.scalar(
        select(HrEmployee).where(
            HrEmployee.organization_id == org.id,
            HrEmployee.employee_code == data.employee_code,
            HrEmployee.document_number == data.document_number,
        )
    )
    if emp is None:
        raise UnauthorizedError("Credenciales no válidas. Verifique sus datos.")
    if emp.status == "terminated":
        raise UnauthorizedError("Este empleado ya no está activo.")

    token, ttl = issue_portal_token(emp.id, org.id)
    portal_emp = await _build_portal_employee(db, org, emp)
    return token, ttl, portal_emp


async def _build_portal_employee(
    db: AsyncSession, org: Organization, emp: HrEmployee,
) -> PortalEmployee:
    dept_name = None
    pos_name = None
    if emp.department_id:
        d = await db.scalar(select(HrDepartment).where(HrDepartment.id == emp.department_id))
        if d:
            dept_name = d.name
    if emp.position_id:
        p = await db.scalar(select(HrPosition).where(HrPosition.id == emp.position_id))
        if p:
            pos_name = p.name
    return PortalEmployee(
        id=emp.id,
        organization_id=org.id,
        employee_code=emp.employee_code,
        first_name=emp.first_name,
        last_name=emp.last_name,
        email=emp.email,
        mobile=emp.mobile,
        address=emp.address,
        department_id=emp.department_id,
        department_name=dept_name,
        position_id=emp.position_id,
        position_name=pos_name,
        hire_date=emp.hire_date,
        employment_type=emp.employment_type,
        work_location=emp.work_location,
        status=emp.status,
        organization_name=org.name,
    )


async def get_portal_employee(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID,
) -> PortalEmployee:
    emp = await db.scalar(
        select(HrEmployee).where(
            HrEmployee.id == employee_id,
            HrEmployee.organization_id == org_id,
        )
    )
    if emp is None:
        raise NotFoundError("Empleado no encontrado.")
    org = await db.scalar(select(Organization).where(Organization.id == org_id))
    if org is None:
        raise NotFoundError("Organización no encontrada.")
    return await _build_portal_employee(db, org, emp)


async def list_portal_contracts(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID,
) -> list[HrContract]:
    rows = await db.execute(
        select(HrContract).where(
            HrContract.organization_id == org_id,
            HrContract.employee_id == employee_id,
        )
        .order_by(HrContract.start_date.desc())
    )
    return list(rows.scalars().all())


async def list_portal_payrolls(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID,
) -> list[dict]:
    """Lista las liquidaciones del empleado de períodos aprobados/pagados/cerrados."""
    rows = await db.execute(
        select(HrPayroll, HrPayrollPeriod)
        .join(HrPayrollPeriod, HrPayrollPeriod.id == HrPayroll.period_id)
        .where(
            HrPayroll.organization_id == org_id,
            HrPayroll.employee_id == employee_id,
            HrPayrollPeriod.status.in_(["approved", "paid", "closed"]),
        )
        .order_by(HrPayrollPeriod.start_date.desc())
    )
    out = []
    for payroll, period in rows.all():
        out.append({
            "id": payroll.id,
            "period_id": period.id,
            "period_code": period.code,
            "period_name": period.name,
            "period_start": period.start_date,
            "period_end": period.end_date,
            "payment_date": period.payment_date,
            "worked_days": payroll.worked_days,
            "total_earnings": payroll.total_earnings,
            "total_deductions": payroll.total_deductions,
            "net_amount": payroll.net_amount,
            "status": payroll.status,
            "paid_at": payroll.paid_at,
        })
    return out


async def get_portal_payroll(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID, payroll_id: uuid.UUID,
) -> HrPayroll:
    p = await db.scalar(
        select(HrPayroll).where(
            HrPayroll.id == payroll_id,
            HrPayroll.organization_id == org_id,
            HrPayroll.employee_id == employee_id,
        )
    )
    if p is None:
        raise NotFoundError("Liquidación no encontrada.")
    return p


async def list_portal_vacation_balances(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID,
) -> list[dict]:
    rows = await db.execute(
        select(HrVacationBalance).where(
            HrVacationBalance.organization_id == org_id,
            HrVacationBalance.employee_id == employee_id,
        )
        .order_by(HrVacationBalance.period_year.desc())
    )
    out = []
    for b in rows.scalars().all():
        avail = (
            Decimal(b.days_accrued or 0)
            - Decimal(b.days_taken or 0)
            - Decimal(b.days_pending or 0)
            - Decimal(b.days_compensated or 0)
        )
        out.append({
            "period_year": b.period_year,
            "days_accrued": b.days_accrued,
            "days_taken": b.days_taken,
            "days_pending": b.days_pending,
            "days_compensated": b.days_compensated,
            "days_available": avail,
        })
    return out


async def list_portal_vacation_requests(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID,
) -> list[HrVacationRequest]:
    rows = await db.execute(
        select(HrVacationRequest).where(
            HrVacationRequest.organization_id == org_id,
            HrVacationRequest.employee_id == employee_id,
        )
        .order_by(HrVacationRequest.requested_at.desc())
    )
    return list(rows.scalars().all())


async def create_portal_vacation_request(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID,
    data: PortalVacationRequestCreate,
) -> HrVacationRequest:
    # Usar el service principal de fase 2 para consistencia
    from src.apps.hr.service_phase2 import (
        VacationRequestsService,
        _next_request_number,
    )
    from src.apps.hr.schemas import VacationRequestCreate

    # No usamos el service porque queremos fuerza employee_id (empleado se auto-solicita)
    number = await _next_request_number(db, org_id)
    r = HrVacationRequest(
        organization_id=org_id,
        employee_id=employee_id,
        request_number=number,
        request_type=data.request_type,
        start_date=data.start_date,
        end_date=data.end_date,
        days_count=data.days_count,
        status="pending",
        request_reason=data.request_reason,
        notes="Solicitada desde portal del empleado",
    )
    db.add(r)
    await db.flush()

    # Reservar saldo en days_pending
    if data.request_type in ("paid", "compensation"):
        from src.apps.hr.service_phase2 import VacationBalancesService
        bal = await VacationBalancesService._get_or_create(
            db, org_id, employee_id, data.start_date.year,
        )
        bal.days_pending = Decimal(bal.days_pending or 0) + Decimal(data.days_count)
    await db.flush()
    await db.refresh(r)
    return r


async def list_portal_leaves(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID,
) -> list[HrLeave]:
    rows = await db.execute(
        select(HrLeave).where(
            HrLeave.organization_id == org_id,
            HrLeave.employee_id == employee_id,
        )
        .order_by(HrLeave.start_date.desc())
    )
    return list(rows.scalars().all())


async def list_portal_evaluations(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID,
) -> list[dict]:
    rows = await db.execute(
        select(HrEvaluation, HrEvaluationCycle)
        .join(HrEvaluationCycle, HrEvaluationCycle.id == HrEvaluation.cycle_id)
        .where(
            HrEvaluation.organization_id == org_id,
            HrEvaluation.employee_id == employee_id,
        )
        .order_by(HrEvaluationCycle.start_date.desc())
    )
    out = []
    for ev, cycle in rows.all():
        out.append({
            "id": ev.id,
            "cycle_id": cycle.id,
            "cycle_name": cycle.name,
            "cycle_code": cycle.code,
            "cycle_period": cycle.period_label,
            "self_completed": ev.self_completed,
            "supervisor_completed": ev.supervisor_completed,
            "overall_score": ev.overall_score,
            "status": ev.status,
            "completed_at": ev.completed_at,
        })
    return out


async def get_portal_evaluation_detail(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID, eval_id: uuid.UUID,
) -> PortalEvaluationDetail:
    ev = await db.scalar(
        select(HrEvaluation).where(
            HrEvaluation.id == eval_id,
            HrEvaluation.organization_id == org_id,
            HrEvaluation.employee_id == employee_id,
        )
    )
    if ev is None:
        raise NotFoundError("Evaluación no encontrada.")
    cycle = await db.scalar(select(HrEvaluationCycle).where(HrEvaluationCycle.id == ev.cycle_id))
    if cycle is None:
        raise NotFoundError("Ciclo no encontrado.")

    competencies = []
    for c in (cycle.competencies or []):
        competencies.append(PortalCompetency(
            code=c.get("code", ""),
            name=c.get("name", ""),
            weight=float(c.get("weight", 1)) if c.get("weight") is not None else None,
            description=c.get("description"),
        ))

    return PortalEvaluationDetail(
        id=ev.id,
        cycle_id=cycle.id,
        cycle_name=cycle.name,
        cycle_code=cycle.code,
        cycle_period=cycle.period_label,
        self_completed=ev.self_completed,
        supervisor_completed=ev.supervisor_completed,
        overall_score=ev.overall_score,
        status=ev.status,
        completed_at=ev.completed_at,
        competencies=competencies,
        scale_min=cycle.scale_min,
        scale_max=cycle.scale_max,
        enable_self=cycle.enable_self,
        enable_supervisor=cycle.enable_supervisor,
        enable_360=cycle.enable_360,
    )


async def submit_portal_evaluation_response(
    db: AsyncSession,
    employee_id: uuid.UUID,
    org_id: uuid.UUID,
    eval_id: uuid.UUID,
    data: PortalEvaluationResponseInput,
) -> HrEvaluationResponse:
    ev = await db.scalar(
        select(HrEvaluation).where(
            HrEvaluation.id == eval_id,
            HrEvaluation.organization_id == org_id,
            HrEvaluation.employee_id == employee_id,
        )
    )
    if ev is None:
        raise NotFoundError("Evaluación no encontrada.")
    cycle = await db.scalar(select(HrEvaluationCycle).where(HrEvaluationCycle.id == ev.cycle_id))
    if cycle is None or cycle.status != "open":
        raise ValidationError("El ciclo no está abierto para recibir respuestas.")

    # Solo self desde portal (la app admin permite supervisor/peer)
    if data.evaluator_type == "self" and not cycle.enable_self:
        raise ValidationError("Auto-evaluación no habilitada para este ciclo.")
    if data.evaluator_type in ("peer", "subordinate") and not cycle.enable_360:
        raise ValidationError("Evaluación 360° no habilitada para este ciclo.")

    # Bloquear duplicado self
    if data.evaluator_type == "self":
        existing = await db.scalar(
            select(HrEvaluationResponse).where(
                HrEvaluationResponse.evaluation_id == eval_id,
                HrEvaluationResponse.evaluator_type == "self",
            )
        )
        if existing is not None:
            raise ConflictError("Ya has enviado tu auto-evaluación.")

    # Calcular overall
    scores = {k: float(v) for k, v in (data.scores or {}).items()}
    weights = {c.get("code"): float(c.get("weight", 1)) for c in (cycle.competencies or [])}
    if scores:
        total_w = sum(weights.get(k, 1) for k in scores.keys())
        if total_w > 0:
            overall = sum(v * weights.get(k, 1) for k, v in scores.items()) / total_w
            overall_d = Decimal(str(round(overall, 2)))
        else:
            overall_d = None
    else:
        overall_d = None

    resp = HrEvaluationResponse(
        organization_id=org_id,
        evaluation_id=eval_id,
        evaluator_type=data.evaluator_type,
        evaluator_employee_id=employee_id,
        scores=scores,
        overall_score=overall_d,
        comments=data.comments,
    )
    db.add(resp)
    await db.flush()

    # Actualizar agregados
    if data.evaluator_type == "self":
        ev.self_completed = True
        ev.self_score = overall_d
    elif data.evaluator_type in ("peer", "subordinate"):
        from sqlalchemy import func
        agg = await db.execute(
            select(
                func.count(HrEvaluationResponse.id),
                func.avg(HrEvaluationResponse.overall_score),
            ).where(
                HrEvaluationResponse.evaluation_id == eval_id,
                HrEvaluationResponse.evaluator_type.in_(["peer", "subordinate"]),
            )
        )
        n, avg = agg.one()
        ev.peer_count = int(n or 0)
        ev.peer_avg = Decimal(str(round(float(avg), 2))) if avg is not None else None

    parts: list[tuple[Decimal, float]] = []
    if ev.self_score is not None:
        parts.append((ev.self_score, 0.30))
    if ev.supervisor_score is not None:
        parts.append((ev.supervisor_score, 0.50))
    if ev.peer_avg is not None:
        parts.append((ev.peer_avg, 0.20))
    if parts:
        total_w = sum(w for _, w in parts)
        o = sum(float(s) * w for s, w in parts) / total_w
        ev.overall_score = Decimal(str(round(o, 2)))

    if ev.self_completed and ev.supervisor_completed:
        ev.status = "completed"
        ev.completed_at = datetime.now(UTC)
    elif ev.self_completed or ev.supervisor_completed or (ev.peer_count and ev.peer_count > 0):
        ev.status = "in_progress"

    await db.flush()
    await db.refresh(resp)
    return resp


async def list_portal_trainings(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID,
) -> list[dict]:
    rows = await db.execute(
        select(HrTrainingEnrollment, HrTrainingCourse)
        .join(HrTrainingCourse, HrTrainingCourse.id == HrTrainingEnrollment.course_id)
        .where(
            HrTrainingEnrollment.organization_id == org_id,
            HrTrainingEnrollment.employee_id == employee_id,
        )
        .order_by(HrTrainingEnrollment.created_at.desc())
    )
    out = []
    for enr, course in rows.all():
        out.append({
            "id": enr.id,
            "course_id": course.id,
            "course_code": course.code,
            "course_name": course.name,
            "course_category": course.category,
            "duration_hours": course.duration_hours,
            "scheduled_date": enr.scheduled_date,
            "completed_date": enr.completed_date,
            "completion_status": enr.completion_status,
            "score": enr.score,
            "certificate_url": enr.certificate_url,
            "certificate_number": enr.certificate_number,
        })
    return out


async def list_portal_documents(
    db: AsyncSession, employee_id: uuid.UUID, org_id: uuid.UUID,
) -> list[HrEmployeeDocument]:
    rows = await db.execute(
        select(HrEmployeeDocument).where(
            HrEmployeeDocument.organization_id == org_id,
            HrEmployeeDocument.employee_id == employee_id,
        )
        .order_by(HrEmployeeDocument.created_at.desc())
    )
    return list(rows.scalars().all())
