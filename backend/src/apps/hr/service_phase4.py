"""SavvyHR · service fase 4 — evaluaciones + capacitaciones + reportes."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from typing import Any

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hr.models import (
    HrAttendance,
    HrDepartment,
    HrEmployee,
    HrEvaluation,
    HrEvaluationCycle,
    HrEvaluationResponse,
    HrLeave,
    HrPayroll,
    HrPayrollPeriod,
    HrTrainingCourse,
    HrTrainingEnrollment,
)
from src.apps.hr.schemas import (
    EvaluationCycleCreate,
    EvaluationCycleUpdate,
    EvaluationResponseInput,
    TrainingCourseCreate,
    TrainingCourseUpdate,
    TrainingEnrollmentCreate,
    TrainingEnrollmentUpdate,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


def _now() -> datetime:
    return datetime.now(UTC)


# ============================================================ Evaluation cycles


class EvaluationCyclesService:

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID, *, status: str | None = None,
    ) -> list[HrEvaluationCycle]:
        stmt = (
            select(HrEvaluationCycle)
            .where(HrEvaluationCycle.organization_id == org_id)
            .order_by(HrEvaluationCycle.start_date.desc())
        )
        if status:
            stmt = stmt.where(HrEvaluationCycle.status == status)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID) -> HrEvaluationCycle:
        c = await db.scalar(
            select(HrEvaluationCycle).where(
                HrEvaluationCycle.id == cid,
                HrEvaluationCycle.organization_id == org_id,
            )
        )
        if c is None:
            raise NotFoundError("Ciclo de evaluación no encontrado.")
        return c

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: EvaluationCycleCreate,
        created_by: uuid.UUID | None,
    ) -> HrEvaluationCycle:
        existing = await db.scalar(
            select(HrEvaluationCycle).where(
                HrEvaluationCycle.organization_id == org_id,
                HrEvaluationCycle.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un ciclo con código '{data.code}'.")
        payload = data.model_dump()
        # Pydantic models en competencias → dicts
        payload["competencies"] = [c if isinstance(c, dict) else c for c in payload.get("competencies", [])]
        # Serializar Decimal en pesos a string para JSONB
        for comp in payload["competencies"]:
            if "weight" in comp and isinstance(comp["weight"], Decimal):
                comp["weight"] = float(comp["weight"])
        cycle = HrEvaluationCycle(
            organization_id=org_id,
            status="draft",
            created_by=created_by,
            **payload,
        )
        db.add(cycle)
        await db.flush()
        await db.refresh(cycle)
        return cycle

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID, data: EvaluationCycleUpdate,
    ) -> HrEvaluationCycle:
        c = await EvaluationCyclesService.get(db, org_id, cid)
        if c.status not in ("draft", "open"):
            raise ValidationError(f"No se puede modificar un ciclo en '{c.status}'.")
        payload = data.model_dump(exclude_unset=True)
        if "competencies" in payload and payload["competencies"] is not None:
            comps = []
            for comp in payload["competencies"]:
                d = comp if isinstance(comp, dict) else dict(comp)
                if "weight" in d and isinstance(d["weight"], Decimal):
                    d["weight"] = float(d["weight"])
                comps.append(d)
            payload["competencies"] = comps
        for k, v in payload.items():
            setattr(c, k, v)
        await db.flush()
        await db.refresh(c)
        return c

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID) -> None:
        c = await EvaluationCyclesService.get(db, org_id, cid)
        if c.status != "draft":
            raise ValidationError("Solo se pueden eliminar ciclos en 'draft'.")
        await db.delete(c)
        await db.flush()

    @staticmethod
    async def open_cycle(
        db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID,
    ) -> dict:
        """Abre el ciclo y crea una HrEvaluation por cada empleado activo."""
        c = await EvaluationCyclesService.get(db, org_id, cid)
        if c.status != "draft":
            raise ValidationError(f"Solo se puede abrir un ciclo en 'draft' (actual: {c.status}).")
        # Crear evaluaciones para todos los empleados activos
        rows = await db.execute(
            select(HrEmployee).where(
                HrEmployee.organization_id == org_id,
                HrEmployee.status == "active",
            )
        )
        emps = list(rows.scalars().all())
        created = 0
        for emp in emps:
            existing = await db.scalar(
                select(HrEvaluation).where(
                    HrEvaluation.cycle_id == c.id,
                    HrEvaluation.employee_id == emp.id,
                )
            )
            if existing is not None:
                continue
            evaluation = HrEvaluation(
                organization_id=org_id,
                cycle_id=c.id,
                employee_id=emp.id,
                supervisor_id=emp.supervisor_id,
                status="pending",
            )
            db.add(evaluation)
            created += 1
        c.status = "open"
        c.opened_at = _now()
        await db.flush()
        await db.refresh(c)
        return {"cycle_id": c.id, "evaluations_created": created, "total_employees": len(emps)}

    @staticmethod
    async def close_cycle(
        db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID,
    ) -> HrEvaluationCycle:
        c = await EvaluationCyclesService.get(db, org_id, cid)
        if c.status != "open":
            raise ValidationError(f"Solo se puede cerrar un ciclo abierto (actual: {c.status}).")
        c.status = "closed"
        c.closed_at = _now()
        await db.flush()
        await db.refresh(c)
        return c


# ============================================================ Evaluations


class EvaluationsService:

    @staticmethod
    async def list_by_cycle(
        db: AsyncSession, org_id: uuid.UUID, cycle_id: uuid.UUID,
    ) -> list[HrEvaluation]:
        rows = await db.execute(
            select(HrEvaluation)
            .where(
                HrEvaluation.organization_id == org_id,
                HrEvaluation.cycle_id == cycle_id,
            )
            .order_by(HrEvaluation.employee_id)
        )
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, eid: uuid.UUID) -> HrEvaluation:
        e = await db.scalar(
            select(HrEvaluation).where(
                HrEvaluation.id == eid,
                HrEvaluation.organization_id == org_id,
            )
        )
        if e is None:
            raise NotFoundError("Evaluación no encontrada.")
        return e

    @staticmethod
    async def get_responses(
        db: AsyncSession, evaluation_id: uuid.UUID,
    ) -> list[HrEvaluationResponse]:
        rows = await db.execute(
            select(HrEvaluationResponse)
            .where(HrEvaluationResponse.evaluation_id == evaluation_id)
            .order_by(HrEvaluationResponse.submitted_at.desc())
        )
        return list(rows.scalars().all())

    @staticmethod
    async def submit_response(
        db: AsyncSession,
        org_id: uuid.UUID,
        evaluation_id: uuid.UUID,
        data: EvaluationResponseInput,
        evaluator_user_id: uuid.UUID | None,
    ) -> HrEvaluationResponse:
        e = await EvaluationsService.get(db, org_id, evaluation_id)
        cycle = await db.scalar(
            select(HrEvaluationCycle).where(HrEvaluationCycle.id == e.cycle_id)
        )
        if cycle is None or cycle.status != "open":
            raise ValidationError("El ciclo no está abierto para recibir respuestas.")

        if data.evaluator_type == "self" and not cycle.enable_self:
            raise ValidationError("Auto-evaluación no habilitada para este ciclo.")
        if data.evaluator_type == "supervisor" and not cycle.enable_supervisor:
            raise ValidationError("Evaluación de jefe no habilitada para este ciclo.")
        if data.evaluator_type in ("peer", "subordinate") and not cycle.enable_360:
            raise ValidationError("Evaluación 360° no habilitada para este ciclo.")

        # Calcular overall_score ponderado según competencias
        scores = data.scores or {}
        weights = {c["code"]: float(c.get("weight", 1)) for c in (cycle.competencies or [])}
        total_w = sum(weights.get(k, 1) * 1 for k in scores.keys()) if scores else 0
        if total_w > 0:
            overall = sum(float(v) * weights.get(k, 1) for k, v in scores.items()) / total_w
            overall_d = Decimal(str(round(overall, 2)))
        else:
            overall_d = None

        # Bloquear duplicado de self/supervisor (una sola respuesta por tipo)
        if data.evaluator_type in ("self", "supervisor"):
            existing = await db.scalar(
                select(HrEvaluationResponse).where(
                    HrEvaluationResponse.evaluation_id == evaluation_id,
                    HrEvaluationResponse.evaluator_type == data.evaluator_type,
                )
            )
            if existing is not None:
                raise ConflictError(
                    f"Ya existe una respuesta de tipo '{data.evaluator_type}' para esta evaluación.",
                )

        resp = HrEvaluationResponse(
            organization_id=org_id,
            evaluation_id=evaluation_id,
            evaluator_type=data.evaluator_type,
            evaluator_user_id=evaluator_user_id,
            evaluator_employee_id=data.evaluator_employee_id,
            scores={k: float(v) for k, v in scores.items()},
            overall_score=overall_d,
            comments=data.comments,
        )
        db.add(resp)
        await db.flush()

        # Recalcular agregados de HrEvaluation
        if data.evaluator_type == "self":
            e.self_completed = True
            e.self_score = overall_d
        elif data.evaluator_type == "supervisor":
            e.supervisor_completed = True
            e.supervisor_score = overall_d
        elif data.evaluator_type in ("peer", "subordinate"):
            # Recalcular peer_count + peer_avg
            agg = await db.execute(
                select(
                    func.count(HrEvaluationResponse.id),
                    func.avg(HrEvaluationResponse.overall_score),
                )
                .where(
                    HrEvaluationResponse.evaluation_id == evaluation_id,
                    HrEvaluationResponse.evaluator_type.in_(["peer", "subordinate"]),
                )
            )
            n, avg = agg.one()
            e.peer_count = int(n or 0)
            e.peer_avg = Decimal(str(round(float(avg), 2))) if avg is not None else None

        # Calcular overall ponderado: self 30%, sup 50%, peer 20% (default)
        parts: list[tuple[Decimal, float]] = []
        if e.self_score is not None:
            parts.append((e.self_score, 0.30))
        if e.supervisor_score is not None:
            parts.append((e.supervisor_score, 0.50))
        if e.peer_avg is not None:
            parts.append((e.peer_avg, 0.20))
        if parts:
            total_w = sum(w for _, w in parts)
            o = sum(float(s) * w for s, w in parts) / total_w
            e.overall_score = Decimal(str(round(o, 2)))

        # Estado de la evaluación
        if e.self_completed and e.supervisor_completed:
            e.status = "completed"
            e.completed_at = _now()
        elif e.self_completed or e.supervisor_completed or (e.peer_count and e.peer_count > 0):
            e.status = "in_progress"

        await db.flush()
        await db.refresh(resp)
        return resp


# ============================================================ Training courses


class TrainingCoursesService:

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID, *, active_only: bool = False,
        category: str | None = None,
    ) -> list[HrTrainingCourse]:
        stmt = (
            select(HrTrainingCourse)
            .where(HrTrainingCourse.organization_id == org_id)
            .order_by(HrTrainingCourse.code)
        )
        if active_only:
            stmt = stmt.where(HrTrainingCourse.is_active.is_(True))
        if category:
            stmt = stmt.where(HrTrainingCourse.category == category)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID) -> HrTrainingCourse:
        c = await db.scalar(
            select(HrTrainingCourse).where(
                HrTrainingCourse.id == cid,
                HrTrainingCourse.organization_id == org_id,
            )
        )
        if c is None:
            raise NotFoundError("Curso no encontrado.")
        return c

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: TrainingCourseCreate,
    ) -> HrTrainingCourse:
        existing = await db.scalar(
            select(HrTrainingCourse).where(
                HrTrainingCourse.organization_id == org_id,
                HrTrainingCourse.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un curso con código '{data.code}'.")
        c = HrTrainingCourse(organization_id=org_id, **data.model_dump())
        db.add(c)
        await db.flush()
        await db.refresh(c)
        return c

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID, data: TrainingCourseUpdate,
    ) -> HrTrainingCourse:
        c = await TrainingCoursesService.get(db, org_id, cid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(c, k, v)
        await db.flush()
        await db.refresh(c)
        return c

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID) -> None:
        c = await TrainingCoursesService.get(db, org_id, cid)
        await db.delete(c)
        await db.flush()


# ============================================================ Training enrollments


class TrainingEnrollmentsService:

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID,
        *, course_id: uuid.UUID | None = None, employee_id: uuid.UUID | None = None,
        status: str | None = None,
    ) -> list[HrTrainingEnrollment]:
        stmt = (
            select(HrTrainingEnrollment)
            .where(HrTrainingEnrollment.organization_id == org_id)
            .order_by(HrTrainingEnrollment.created_at.desc())
        )
        if course_id:
            stmt = stmt.where(HrTrainingEnrollment.course_id == course_id)
        if employee_id:
            stmt = stmt.where(HrTrainingEnrollment.employee_id == employee_id)
        if status:
            stmt = stmt.where(HrTrainingEnrollment.completion_status == status)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: TrainingEnrollmentCreate,
        enrolled_by: uuid.UUID | None,
    ) -> HrTrainingEnrollment:
        course = await db.scalar(
            select(HrTrainingCourse).where(
                HrTrainingCourse.id == data.course_id,
                HrTrainingCourse.organization_id == org_id,
            )
        )
        if course is None:
            raise NotFoundError("Curso no encontrado.")
        emp = await db.scalar(
            select(HrEmployee).where(
                HrEmployee.id == data.employee_id,
                HrEmployee.organization_id == org_id,
            )
        )
        if emp is None:
            raise NotFoundError("Empleado no encontrado.")
        e = HrTrainingEnrollment(
            organization_id=org_id,
            completion_status="enrolled",
            cost=course.cost_per_seat,
            enrolled_by=enrolled_by,
            **data.model_dump(),
        )
        db.add(e)
        await db.flush()
        await db.refresh(e)
        return e

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, eid: uuid.UUID, data: TrainingEnrollmentUpdate,
    ) -> HrTrainingEnrollment:
        e = await db.scalar(
            select(HrTrainingEnrollment).where(
                HrTrainingEnrollment.id == eid,
                HrTrainingEnrollment.organization_id == org_id,
            )
        )
        if e is None:
            raise NotFoundError("Inscripción no encontrada.")
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(e, k, v)
        if e.completion_status == "completed" and e.completed_date is None:
            e.completed_date = date.today()
        await db.flush()
        await db.refresh(e)
        return e

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, eid: uuid.UUID) -> None:
        e = await db.scalar(
            select(HrTrainingEnrollment).where(
                HrTrainingEnrollment.id == eid,
                HrTrainingEnrollment.organization_id == org_id,
            )
        )
        if e is None:
            raise NotFoundError("Inscripción no encontrada.")
        await db.delete(e)
        await db.flush()


# ============================================================ Reports


class ReportsService:

    @staticmethod
    async def headcount_by_department(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> dict:
        rows = await db.execute(
            select(
                HrDepartment.id,
                HrDepartment.name,
                func.count(HrEmployee.id).label("n"),
            )
            .where(HrEmployee.organization_id == org_id, HrEmployee.status == "active")
            .outerjoin(HrDepartment, HrDepartment.id == HrEmployee.department_id)
            .group_by(HrDepartment.id, HrDepartment.name)
            .order_by(func.count(HrEmployee.id).desc())
        )
        items = list(rows.all())
        total = sum(int(r.n) for r in items)
        result_rows = []
        for r in items:
            n = int(r.n)
            result_rows.append({
                "label": r.name or "Sin departamento",
                "count": n,
                "percentage": round((n / total * 100) if total else 0, 2),
            })
        return {"total": total, "rows": result_rows}

    @staticmethod
    async def tenure_distribution(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> dict:
        rows = await db.execute(
            select(HrEmployee.hire_date).where(
                HrEmployee.organization_id == org_id,
                HrEmployee.status == "active",
            )
        )
        hire_dates = [r[0] for r in rows.all()]
        today = date.today()
        years = [
            ((today - h).days / 365.25) for h in hire_dates if h is not None
        ]
        total = len(years)
        avg = round(sum(years) / total, 2) if total else 0

        buckets_def = [
            ("< 1 año", 0, 1),
            ("1-2 años", 1, 2),
            ("2-5 años", 2, 5),
            ("5-10 años", 5, 10),
            ("10+ años", 10, None),
        ]
        result = []
        for label, mn, mx in buckets_def:
            if mx is None:
                n = sum(1 for y in years if y >= mn)
            else:
                n = sum(1 for y in years if mn <= y < mx)
            result.append({"label": label, "min_years": mn, "max_years": mx, "count": n})
        return {"total": total, "avg_years": avg, "buckets": result}

    @staticmethod
    async def cost_by_department(
        db: AsyncSession, org_id: uuid.UUID, period_id: uuid.UUID,
    ) -> dict:
        period = await db.scalar(
            select(HrPayrollPeriod).where(
                HrPayrollPeriod.id == period_id,
                HrPayrollPeriod.organization_id == org_id,
            )
        )
        if period is None:
            raise NotFoundError("Período de nómina no encontrado.")

        rows = await db.execute(
            select(
                HrPayroll.department_name,
                func.count(HrPayroll.id).label("n"),
                func.sum(HrPayroll.total_earnings).label("cost"),
            )
            .where(
                HrPayroll.organization_id == org_id,
                HrPayroll.period_id == period_id,
            )
            .group_by(HrPayroll.department_name)
            .order_by(func.sum(HrPayroll.total_earnings).desc())
        )
        result_rows = []
        total = Decimal("0")
        for r in rows.all():
            cost = Decimal(r.cost or 0)
            total += cost
            result_rows.append({
                "department_id": None,
                "department_name": r.department_name or "Sin departamento",
                "employee_count": int(r.n),
                "total_cost": cost,
            })
        return {
            "period_id": period.id,
            "period_code": period.code,
            "total": total,
            "rows": result_rows,
        }

    @staticmethod
    async def absenteeism(
        db: AsyncSession, org_id: uuid.UUID, date_from: date, date_to: date,
    ) -> dict:
        # Asistencia
        att_rows = await db.execute(
            select(
                HrAttendance.employee_id,
                HrEmployee.employee_code,
                (HrEmployee.first_name + " " + func.coalesce(HrEmployee.last_name, "")).label("name"),
                func.sum(func.cast(HrAttendance.status == "absent", type_=func.coalesce(func.count(1), 0).type)).label("absent"),
            )
            .where(
                HrAttendance.organization_id == org_id,
                HrAttendance.work_date >= date_from,
                HrAttendance.work_date <= date_to,
            )
            .join(HrEmployee, HrEmployee.id == HrAttendance.employee_id)
            .group_by(HrAttendance.employee_id, HrEmployee.employee_code, HrEmployee.first_name, HrEmployee.last_name)
        )
        # Simplificación: usamos conteo manual por status
        emps = {}
        rows_simple = await db.execute(
            select(
                HrAttendance.employee_id,
                HrEmployee.employee_code,
                HrEmployee.first_name,
                HrEmployee.last_name,
                HrAttendance.status,
            )
            .where(
                HrAttendance.organization_id == org_id,
                HrAttendance.work_date >= date_from,
                HrAttendance.work_date <= date_to,
            )
            .join(HrEmployee, HrEmployee.id == HrAttendance.employee_id)
        )
        for r in rows_simple.all():
            key = r.employee_id
            if key not in emps:
                emps[key] = {
                    "employee_id": r.employee_id,
                    "employee_code": r.employee_code,
                    "employee_name": f"{r.first_name} {r.last_name or ''}".strip(),
                    "absent_days": 0.0,
                    "late_days": 0.0,
                    "leave_days": 0.0,
                }
            if r.status == "absent":
                emps[key]["absent_days"] += 1
            elif r.status == "late":
                emps[key]["late_days"] += 1
            elif r.status in ("sick_leave", "permit", "vacation"):
                emps[key]["leave_days"] += 1

        # Leaves del período
        leave_rows = await db.execute(
            select(HrLeave.employee_id, HrLeave.days_count, HrEmployee.employee_code, HrEmployee.first_name, HrEmployee.last_name)
            .where(
                HrLeave.organization_id == org_id,
                HrLeave.start_date <= date_to,
                HrLeave.end_date >= date_from,
                HrLeave.status == "active",
            )
            .join(HrEmployee, HrEmployee.id == HrLeave.employee_id)
        )
        for r in leave_rows.all():
            key = r.employee_id
            if key not in emps:
                emps[key] = {
                    "employee_id": r.employee_id,
                    "employee_code": r.employee_code,
                    "employee_name": f"{r.first_name} {r.last_name or ''}".strip(),
                    "absent_days": 0.0,
                    "late_days": 0.0,
                    "leave_days": 0.0,
                }
            emps[key]["leave_days"] += float(r.days_count or 0)

        rows_out = []
        for row in emps.values():
            row["total_days"] = row["absent_days"] + row["late_days"] + row["leave_days"]
            rows_out.append(row)
        rows_out.sort(key=lambda x: x["total_days"], reverse=True)
        return {"date_from": date_from, "date_to": date_to, "rows": rows_out}

    @staticmethod
    async def training_summary(
        db: AsyncSession, org_id: uuid.UUID,
    ) -> list[dict]:
        courses = await db.execute(
            select(HrTrainingCourse).where(HrTrainingCourse.organization_id == org_id)
        )
        out = []
        for c in courses.scalars().all():
            rows = await db.execute(
                select(HrTrainingEnrollment).where(
                    HrTrainingEnrollment.course_id == c.id,
                    HrTrainingEnrollment.organization_id == org_id,
                )
            )
            enrolls = list(rows.scalars().all())
            completed = [e for e in enrolls if e.completion_status == "completed"]
            in_prog = [e for e in enrolls if e.completion_status == "in_progress"]
            scores = [float(e.score) for e in completed if e.score is not None]
            avg = round(sum(scores) / len(scores), 2) if scores else None
            total_cost = sum(Decimal(e.cost or 0) for e in enrolls)
            out.append({
                "course_id": c.id,
                "course_code": c.code,
                "course_name": c.name,
                "enrollments": len(enrolls),
                "completed": len(completed),
                "in_progress": len(in_prog),
                "avg_score": avg,
                "total_cost": total_cost,
            })
        return out
