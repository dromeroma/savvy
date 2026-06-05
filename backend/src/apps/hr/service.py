"""SavvyHR services — fase 1: lógica CRUD para los 5 recursos."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.hr.models import (
    HrContract,
    HrDepartment,
    HrEmployee,
    HrEmployeeDocument,
    HrPosition,
)
from src.apps.hr.schemas import (
    ContractCreate,
    ContractUpdate,
    DepartmentCreate,
    DepartmentUpdate,
    DocumentCreate,
    DocumentUpdate,
    EmployeeCreate,
    EmployeeUpdate,
    PositionCreate,
    PositionUpdate,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ============================================================ Departments


class DepartmentsService:

    @staticmethod
    async def list_(db: AsyncSession, org_id: uuid.UUID, active_only: bool = False):
        stmt = (
            select(HrDepartment)
            .where(HrDepartment.organization_id == org_id)
            .order_by(HrDepartment.code)
        )
        if active_only:
            stmt = stmt.where(HrDepartment.is_active.is_(True))
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, did: uuid.UUID) -> HrDepartment:
        d = await db.scalar(
            select(HrDepartment).where(
                HrDepartment.id == did,
                HrDepartment.organization_id == org_id,
            )
        )
        if d is None:
            raise NotFoundError("Departamento no encontrado.")
        return d

    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, data: DepartmentCreate) -> HrDepartment:
        existing = await db.scalar(
            select(HrDepartment).where(
                HrDepartment.organization_id == org_id,
                HrDepartment.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un departamento con código '{data.code}'.")
        if data.parent_id is not None:
            await DepartmentsService.get(db, org_id, data.parent_id)
        d = HrDepartment(organization_id=org_id, **data.model_dump())
        db.add(d)
        await db.flush()
        await db.refresh(d)
        return d

    @staticmethod
    async def update(db: AsyncSession, org_id: uuid.UUID, did: uuid.UUID, data: DepartmentUpdate) -> HrDepartment:
        d = await DepartmentsService.get(db, org_id, did)
        payload = data.model_dump(exclude_unset=True)
        if payload.get("parent_id") == did:
            raise ValidationError("Un departamento no puede ser su propio padre.")
        for k, v in payload.items():
            setattr(d, k, v)
        await db.flush()
        await db.refresh(d)
        return d

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, did: uuid.UUID) -> None:
        d = await DepartmentsService.get(db, org_id, did)
        await db.delete(d)
        await db.flush()


# ============================================================ Positions


class PositionsService:

    @staticmethod
    async def list_(db: AsyncSession, org_id: uuid.UUID, active_only: bool = False, department_id: uuid.UUID | None = None):
        stmt = (
            select(HrPosition)
            .where(HrPosition.organization_id == org_id)
            .order_by(HrPosition.code)
        )
        if active_only:
            stmt = stmt.where(HrPosition.is_active.is_(True))
        if department_id is not None:
            stmt = stmt.where(HrPosition.department_id == department_id)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID) -> HrPosition:
        p = await db.scalar(
            select(HrPosition).where(
                HrPosition.id == pid,
                HrPosition.organization_id == org_id,
            )
        )
        if p is None:
            raise NotFoundError("Cargo no encontrado.")
        return p

    @staticmethod
    async def create(db: AsyncSession, org_id: uuid.UUID, data: PositionCreate) -> HrPosition:
        existing = await db.scalar(
            select(HrPosition).where(
                HrPosition.organization_id == org_id,
                HrPosition.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un cargo con código '{data.code}'.")
        if data.min_salary is not None and data.max_salary is not None and data.min_salary > data.max_salary:
            raise ValidationError("El salario mínimo no puede ser mayor al máximo.")
        p = HrPosition(organization_id=org_id, **data.model_dump())
        db.add(p)
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def update(db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID, data: PositionUpdate) -> HrPosition:
        p = await PositionsService.get(db, org_id, pid)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(p, k, v)
        if p.min_salary is not None and p.max_salary is not None and p.min_salary > p.max_salary:
            raise ValidationError("El salario mínimo no puede ser mayor al máximo.")
        await db.flush()
        await db.refresh(p)
        return p

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, pid: uuid.UUID) -> None:
        p = await PositionsService.get(db, org_id, pid)
        await db.delete(p)
        await db.flush()


# ============================================================ Employees


class EmployeesService:

    @staticmethod
    async def list_(
        db: AsyncSession,
        org_id: uuid.UUID,
        *,
        status: str | None = None,
        department_id: uuid.UUID | None = None,
        position_id: uuid.UUID | None = None,
        search: str | None = None,
    ):
        stmt = (
            select(
                HrEmployee.id,
                HrEmployee.employee_code,
                HrEmployee.first_name,
                HrEmployee.last_name,
                HrEmployee.document_number,
                HrEmployee.email,
                HrEmployee.mobile,
                HrEmployee.department_id,
                HrDepartment.name.label("department_name"),
                HrEmployee.position_id,
                HrPosition.name.label("position_name"),
                HrEmployee.hire_date,
                HrEmployee.status,
                HrEmployee.employment_type,
            )
            .where(HrEmployee.organization_id == org_id)
            .outerjoin(HrDepartment, HrDepartment.id == HrEmployee.department_id)
            .outerjoin(HrPosition, HrPosition.id == HrEmployee.position_id)
            .order_by(HrEmployee.employee_code)
        )
        if status:
            stmt = stmt.where(HrEmployee.status == status)
        if department_id:
            stmt = stmt.where(HrEmployee.department_id == department_id)
        if position_id:
            stmt = stmt.where(HrEmployee.position_id == position_id)
        if search:
            like = f"%{search.strip()}%"
            stmt = stmt.where(
                or_(
                    HrEmployee.first_name.ilike(like),
                    HrEmployee.last_name.ilike(like),
                    HrEmployee.employee_code.ilike(like),
                    HrEmployee.email.ilike(like),
                    HrEmployee.mobile.ilike(like),
                    HrEmployee.document_number.ilike(like),
                )
            )
        rows = await db.execute(stmt)
        return [dict(r._mapping) for r in rows.all()]

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, eid: uuid.UUID) -> HrEmployee:
        e = await db.scalar(
            select(HrEmployee).where(
                HrEmployee.id == eid,
                HrEmployee.organization_id == org_id,
            )
        )
        if e is None:
            raise NotFoundError("Empleado no encontrado.")
        return e

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: EmployeeCreate, created_by: uuid.UUID | None,
    ) -> HrEmployee:
        existing = await db.scalar(
            select(HrEmployee).where(
                HrEmployee.organization_id == org_id,
                HrEmployee.employee_code == data.employee_code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un empleado con código '{data.employee_code}'.")
        if data.person_id is not None:
            dup = await db.scalar(
                select(HrEmployee).where(
                    HrEmployee.organization_id == org_id,
                    HrEmployee.person_id == data.person_id,
                )
            )
            if dup is not None:
                raise ConflictError("Esa persona ya está registrada como empleado.")
        if data.department_id:
            d = await db.scalar(
                select(HrDepartment).where(
                    HrDepartment.id == data.department_id,
                    HrDepartment.organization_id == org_id,
                )
            )
            if d is None:
                raise NotFoundError("Departamento no encontrado.")
        if data.position_id:
            p = await db.scalar(
                select(HrPosition).where(
                    HrPosition.id == data.position_id,
                    HrPosition.organization_id == org_id,
                )
            )
            if p is None:
                raise NotFoundError("Cargo no encontrado.")
        e = HrEmployee(
            organization_id=org_id,
            created_by=created_by,
            **data.model_dump(),
        )
        db.add(e)
        await db.flush()
        await db.refresh(e)
        return e

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, eid: uuid.UUID, data: EmployeeUpdate,
    ) -> HrEmployee:
        e = await EmployeesService.get(db, org_id, eid)
        payload = data.model_dump(exclude_unset=True)
        # Si se marca como terminado y no hay fecha, ponemos la de hoy
        if payload.get("status") == "terminated" and not payload.get("termination_date"):
            from datetime import date as _date
            payload["termination_date"] = _date.today()
        for k, v in payload.items():
            setattr(e, k, v)
        await db.flush()
        await db.refresh(e)
        return e

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, eid: uuid.UUID) -> None:
        e = await EmployeesService.get(db, org_id, eid)
        await db.delete(e)
        await db.flush()


# ============================================================ Contracts


class ContractsService:

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID,
        *, employee_id: uuid.UUID | None = None, status: str | None = None,
    ):
        stmt = (
            select(HrContract)
            .where(HrContract.organization_id == org_id)
            .order_by(HrContract.start_date.desc())
        )
        if employee_id:
            stmt = stmt.where(HrContract.employee_id == employee_id)
        if status:
            stmt = stmt.where(HrContract.status == status)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID) -> HrContract:
        c = await db.scalar(
            select(HrContract).where(
                HrContract.id == cid,
                HrContract.organization_id == org_id,
            )
        )
        if c is None:
            raise NotFoundError("Contrato no encontrado.")
        return c

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: ContractCreate, created_by: uuid.UUID | None,
    ) -> HrContract:
        emp = await db.scalar(
            select(HrEmployee).where(
                HrEmployee.id == data.employee_id,
                HrEmployee.organization_id == org_id,
            )
        )
        if emp is None:
            raise NotFoundError("Empleado no encontrado.")
        existing = await db.scalar(
            select(HrContract).where(
                HrContract.organization_id == org_id,
                HrContract.contract_number == data.contract_number,
            )
        )
        if existing is not None:
            raise ConflictError(
                f"Ya existe un contrato con número '{data.contract_number}'."
            )
        if data.contract_type == "fijo" and data.end_date is None:
            raise ValidationError("Los contratos a término fijo deben tener fecha de fin.")
        if data.end_date and data.end_date < data.start_date:
            raise ValidationError("La fecha de fin no puede ser anterior al inicio.")
        c = HrContract(
            organization_id=org_id,
            created_by=created_by,
            status="active",
            renewal_count=0,
            **data.model_dump(),
        )
        db.add(c)
        await db.flush()
        await db.refresh(c)
        return c

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID, data: ContractUpdate,
    ) -> HrContract:
        c = await ContractsService.get(db, org_id, cid)
        payload = data.model_dump(exclude_unset=True)
        if payload.get("status") == "terminated" and c.terminated_at is None:
            c.terminated_at = _now_utc()
        for k, v in payload.items():
            setattr(c, k, v)
        if c.end_date and c.end_date < c.start_date:
            raise ValidationError("La fecha de fin no puede ser anterior al inicio.")
        await db.flush()
        await db.refresh(c)
        return c

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, cid: uuid.UUID) -> None:
        c = await ContractsService.get(db, org_id, cid)
        await db.delete(c)
        await db.flush()


# ============================================================ Documents


class DocumentsService:

    @staticmethod
    async def list_(
        db: AsyncSession, org_id: uuid.UUID,
        *, employee_id: uuid.UUID | None = None, document_type: str | None = None,
    ):
        stmt = (
            select(HrEmployeeDocument)
            .where(HrEmployeeDocument.organization_id == org_id)
            .order_by(HrEmployeeDocument.created_at.desc())
        )
        if employee_id:
            stmt = stmt.where(HrEmployeeDocument.employee_id == employee_id)
        if document_type:
            stmt = stmt.where(HrEmployeeDocument.document_type == document_type)
        rows = await db.execute(stmt)
        return list(rows.scalars().all())

    @staticmethod
    async def get(db: AsyncSession, org_id: uuid.UUID, did: uuid.UUID) -> HrEmployeeDocument:
        d = await db.scalar(
            select(HrEmployeeDocument).where(
                HrEmployeeDocument.id == did,
                HrEmployeeDocument.organization_id == org_id,
            )
        )
        if d is None:
            raise NotFoundError("Documento no encontrado.")
        return d

    @staticmethod
    async def create(
        db: AsyncSession, org_id: uuid.UUID, data: DocumentCreate, uploaded_by: uuid.UUID | None,
    ) -> HrEmployeeDocument:
        emp = await db.scalar(
            select(HrEmployee).where(
                HrEmployee.id == data.employee_id,
                HrEmployee.organization_id == org_id,
            )
        )
        if emp is None:
            raise NotFoundError("Empleado no encontrado.")
        doc = HrEmployeeDocument(
            organization_id=org_id,
            uploaded_by=uploaded_by,
            status="valid",
            **data.model_dump(),
        )
        db.add(doc)
        await db.flush()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def update(
        db: AsyncSession, org_id: uuid.UUID, did: uuid.UUID, data: DocumentUpdate,
    ) -> HrEmployeeDocument:
        doc = await DocumentsService.get(db, org_id, did)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(doc, k, v)
        await db.flush()
        await db.refresh(doc)
        return doc

    @staticmethod
    async def delete(db: AsyncSession, org_id: uuid.UUID, did: uuid.UUID) -> None:
        doc = await DocumentsService.get(db, org_id, did)
        await db.delete(doc)
        await db.flush()
