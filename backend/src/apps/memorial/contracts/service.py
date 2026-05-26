"""Lógica de negocio para contratos exequiales."""

from __future__ import annotations

import uuid
from datetime import UTC, date, datetime
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.contracts.schemas import (
    BeneficiaryCreate,
    BeneficiaryUpdate,
    ContractCreate,
    ContractListItem,
    ContractUpdate,
    CoverageLookupResult,
    TransitionRequest,
)
from src.apps.memorial.models import (
    MemorialExequialBeneficiary,
    MemorialExequialContract,
    MemorialExequialPlan,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


# Mapeo frecuencia → meses entre cuotas
FREQUENCY_MONTHS: dict[str, int] = {
    "monthly": 1,
    "quarterly": 3,
    "semiannual": 6,
    "annual": 12,
}

# Transiciones legales entre estados de contrato
LEGAL_TRANSITIONS: dict[str, set[str]] = {
    "active": {"suspended", "cancelled", "expired"},
    "suspended": {"active", "cancelled"},
    "cancelled": set(),
    "expired": {"active", "cancelled"},   # se permite reactivar tras vencimiento
}


def _add_months(d: date, months: int) -> date:
    """Suma N meses a una fecha cuidando el día final (ej. 31 ene + 1 mes = 28/29 feb)."""
    total = d.month + months
    new_year = d.year + (total - 1) // 12
    new_month = ((total - 1) % 12) + 1
    # Ajustar día si el mes destino no tiene tantos días
    if new_month == 2:
        last_day = 29 if (new_year % 4 == 0 and (new_year % 100 != 0 or new_year % 400 == 0)) else 28
    elif new_month in (4, 6, 9, 11):
        last_day = 30
    else:
        last_day = 31
    return date(new_year, new_month, min(d.day, last_day))


def _fee_for_frequency(plan: MemorialExequialPlan, freq: str) -> Decimal:
    return {
        "monthly": Decimal(plan.monthly_fee),
        "quarterly": Decimal(plan.quarterly_fee),
        "semiannual": Decimal(plan.semiannual_fee),
        "annual": Decimal(plan.annual_fee),
    }[freq]


def _titular_display(c: MemorialExequialContract) -> str:
    if c.affiliate_type == "empresarial":
        return c.titular_business_name or "(empresa sin nombre)"
    parts = [c.titular_first_name or "", c.titular_last_name or ""]
    return " ".join(p for p in parts if p).strip() or "(titular sin nombre)"


class ContractsService:

    # ------------------------------------------------------------------
    # Listing / detail
    # ------------------------------------------------------------------
    @staticmethod
    async def list_contracts(
        db: AsyncSession,
        org_id: uuid.UUID,
        search: str | None = None,
        status_: str | None = None,
        plan_id: uuid.UUID | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ContractListItem]:
        ben_count_sq = (
            select(
                MemorialExequialBeneficiary.contract_id,
                func.count(MemorialExequialBeneficiary.id).label("n"),
            )
            .where(
                MemorialExequialBeneficiary.organization_id == org_id,
                MemorialExequialBeneficiary.removed_at.is_(None),
            )
            .group_by(MemorialExequialBeneficiary.contract_id)
            .subquery()
        )
        stmt = (
            select(
                MemorialExequialContract,
                MemorialExequialPlan.name.label("plan_name"),
                func.coalesce(ben_count_sq.c.n, 0).label("ben_count"),
            )
            .join(MemorialExequialPlan, MemorialExequialPlan.id == MemorialExequialContract.plan_id)
            .outerjoin(ben_count_sq, ben_count_sq.c.contract_id == MemorialExequialContract.id)
            .where(MemorialExequialContract.organization_id == org_id)
            .order_by(MemorialExequialContract.consecutive.desc())
            .limit(limit)
            .offset(offset)
        )
        if status_:
            stmt = stmt.where(MemorialExequialContract.status == status_)
        if plan_id:
            stmt = stmt.where(MemorialExequialContract.plan_id == plan_id)
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(MemorialExequialContract.code).like(like),
                    func.lower(func.coalesce(MemorialExequialContract.titular_first_name, "")).like(like),
                    func.lower(func.coalesce(MemorialExequialContract.titular_last_name, "")).like(like),
                    func.lower(func.coalesce(MemorialExequialContract.titular_business_name, "")).like(like),
                    func.lower(func.coalesce(MemorialExequialContract.titular_document_number, "")).like(like),
                )
            )
        rows = await db.execute(stmt)
        out: list[ContractListItem] = []
        for c, plan_name, ben_count in rows.all():
            out.append(ContractListItem(
                id=c.id, code=c.code, consecutive=c.consecutive,
                plan_id=c.plan_id, plan_name=plan_name,
                affiliate_type=c.affiliate_type,
                titular_display=_titular_display(c),
                titular_document_number=c.titular_document_number,
                payment_frequency=c.payment_frequency,
                fee_amount=c.fee_amount,
                start_date=c.start_date,
                next_payment_date=c.next_payment_date,
                status=c.status,
                beneficiaries_count=int(ben_count),
            ))
        return out

    @staticmethod
    async def get_contract(
        db: AsyncSession, org_id: uuid.UUID, contract_id: uuid.UUID,
    ) -> MemorialExequialContract:
        c = await db.scalar(
            select(MemorialExequialContract).where(
                MemorialExequialContract.id == contract_id,
                MemorialExequialContract.organization_id == org_id,
            )
        )
        if c is None:
            raise NotFoundError("Contrato exequial no encontrado.")
        return c

    @staticmethod
    async def get_contract_with_relations(
        db: AsyncSession, org_id: uuid.UUID, contract_id: uuid.UUID,
    ) -> tuple[MemorialExequialContract, MemorialExequialPlan, list[MemorialExequialBeneficiary]]:
        c = await ContractsService.get_contract(db, org_id, contract_id)
        plan = await db.get(MemorialExequialPlan, c.plan_id)
        rows = await db.execute(
            select(MemorialExequialBeneficiary)
            .where(MemorialExequialBeneficiary.contract_id == c.id)
            .order_by(
                MemorialExequialBeneficiary.is_titular.desc(),
                MemorialExequialBeneficiary.created_at,
            )
        )
        beneficiaries = list(rows.scalars().all())
        return c, plan, beneficiaries

    # ------------------------------------------------------------------
    # Create / update
    # ------------------------------------------------------------------
    @staticmethod
    async def _next_consecutive(db: AsyncSession, org_id: uuid.UUID) -> int:
        last = await db.scalar(
            select(func.coalesce(func.max(MemorialExequialContract.consecutive), 0))
            .where(MemorialExequialContract.organization_id == org_id)
        )
        return int(last) + 1

    @staticmethod
    async def create_contract(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: ContractCreate,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialExequialContract:
        # Plan existe y está activo
        plan = await db.scalar(
            select(MemorialExequialPlan).where(
                MemorialExequialPlan.id == data.plan_id,
                MemorialExequialPlan.organization_id == org_id,
            )
        )
        if plan is None:
            raise NotFoundError("Plan exequial no encontrado.")
        if not plan.is_active:
            raise ValidationError("El plan está inactivo; no se pueden firmar contratos.")
        # Tipo de afiliado compatible con plan
        if plan.plan_type != data.affiliate_type:
            raise ValidationError(
                f"El plan '{plan.code}' es de tipo '{plan.plan_type}' pero el contrato "
                f"es '{data.affiliate_type}'.",
            )
        # max_beneficiaries
        if (
            plan.max_beneficiaries is not None
            and len(data.beneficiaries) > plan.max_beneficiaries
        ):
            raise ValidationError(
                f"Este plan permite máximo {plan.max_beneficiaries} beneficiarios "
                f"(recibidos {len(data.beneficiaries)}).",
            )

        consec = await ContractsService._next_consecutive(db, org_id)
        fee = _fee_for_frequency(plan, data.payment_frequency)
        if fee <= 0:
            raise ValidationError(
                f"El plan no tiene tarifa configurada para frecuencia '{data.payment_frequency}'.",
            )

        next_pay = _add_months(data.start_date, FREQUENCY_MONTHS[data.payment_frequency])

        payload = data.model_dump(exclude={"beneficiaries"})
        contract = MemorialExequialContract(
            organization_id=org_id,
            consecutive=consec,
            code=f"EXQ-{consec:04d}",
            fee_amount=fee,
            next_payment_date=next_pay,
            status="active",
            created_by=actor_user_id,
            **payload,
        )
        db.add(contract)
        await db.flush()

        # Beneficiarios — solo uno con is_titular=True
        has_titular = False
        for b in data.beneficiaries:
            ben = MemorialExequialBeneficiary(
                organization_id=org_id,
                contract_id=contract.id,
                first_name=b.first_name,
                last_name=b.last_name,
                document_type=b.document_type,
                document_number=b.document_number,
                birth_date=b.birth_date,
                gender=b.gender,
                is_titular=b.is_titular,
                joined_at=b.joined_at or contract.start_date,
            )
            ben.relationship_ = b.relationship
            if b.is_titular:
                if has_titular:
                    raise ValidationError("Solo un beneficiario puede marcarse como titular.")
                has_titular = True
            db.add(ben)
        await db.flush()
        return contract

    @staticmethod
    async def update_contract(
        db: AsyncSession,
        org_id: uuid.UUID,
        contract_id: uuid.UUID,
        data: ContractUpdate,
    ) -> MemorialExequialContract:
        c = await ContractsService.get_contract(db, org_id, contract_id)
        if c.status == "cancelled":
            raise ConflictError("No se puede editar un contrato cancelado.")
        changes = data.model_dump(exclude_unset=True)

        # Si cambia la frecuencia, recalcular fee_amount automáticamente
        if "payment_frequency" in changes and "fee_amount" not in changes:
            plan = await db.get(MemorialExequialPlan, c.plan_id)
            if plan is not None:
                changes["fee_amount"] = _fee_for_frequency(plan, changes["payment_frequency"])

        for k, v in changes.items():
            setattr(c, k, v)
        await db.flush()
        return c

    @staticmethod
    async def transition_status(
        db: AsyncSession,
        org_id: uuid.UUID,
        contract_id: uuid.UUID,
        req: TransitionRequest,
    ) -> MemorialExequialContract:
        c = await ContractsService.get_contract(db, org_id, contract_id)
        old, new = c.status, req.new_status
        if new == old:
            raise ConflictError(f"El contrato ya está en estado '{old}'.")
        allowed = LEGAL_TRANSITIONS.get(old, set())
        if new not in allowed:
            raise ValidationError(
                f"Transición no permitida: {old} → {new}. "
                f"Estados destino válidos: {', '.join(sorted(allowed)) or '(ninguno)'}.",
            )
        now = datetime.now(UTC)
        c.status = new
        if new == "suspended":
            c.suspended_at = now
        elif new == "cancelled":
            c.cancelled_at = now
            c.cancellation_reason = req.reason
        elif new == "active":
            # Reactivar: limpiar suspensión
            c.suspended_at = None
        await db.flush()
        return c

    # ------------------------------------------------------------------
    # Beneficiaries
    # ------------------------------------------------------------------
    @staticmethod
    async def add_beneficiary(
        db: AsyncSession,
        org_id: uuid.UUID,
        contract_id: uuid.UUID,
        data: BeneficiaryCreate,
    ) -> MemorialExequialBeneficiary:
        c = await ContractsService.get_contract(db, org_id, contract_id)
        if data.is_titular:
            # quitarle titular al actual
            await ContractsService._clear_titular(db, org_id, contract_id)
        ben = MemorialExequialBeneficiary(
            organization_id=org_id,
            contract_id=c.id,
            first_name=data.first_name,
            last_name=data.last_name,
            document_type=data.document_type,
            document_number=data.document_number,
            birth_date=data.birth_date,
            gender=data.gender,
            is_titular=data.is_titular,
            joined_at=data.joined_at or date.today(),
        )
        ben.relationship_ = data.relationship
        db.add(ben)
        await db.flush()
        return ben

    @staticmethod
    async def update_beneficiary(
        db: AsyncSession,
        org_id: uuid.UUID,
        contract_id: uuid.UUID,
        beneficiary_id: uuid.UUID,
        data: BeneficiaryUpdate,
    ) -> MemorialExequialBeneficiary:
        ben = await db.scalar(
            select(MemorialExequialBeneficiary).where(
                MemorialExequialBeneficiary.id == beneficiary_id,
                MemorialExequialBeneficiary.contract_id == contract_id,
                MemorialExequialBeneficiary.organization_id == org_id,
            )
        )
        if ben is None:
            raise NotFoundError("Beneficiario no encontrado.")
        changes = data.model_dump(exclude_unset=True)
        if changes.get("is_titular") is True:
            await ContractsService._clear_titular(db, org_id, contract_id)
        if "relationship" in changes:
            ben.relationship_ = changes.pop("relationship")
        for k, v in changes.items():
            setattr(ben, k, v)
        await db.flush()
        return ben

    @staticmethod
    async def remove_beneficiary(
        db: AsyncSession,
        org_id: uuid.UUID,
        contract_id: uuid.UUID,
        beneficiary_id: uuid.UUID,
    ) -> None:
        ben = await db.scalar(
            select(MemorialExequialBeneficiary).where(
                MemorialExequialBeneficiary.id == beneficiary_id,
                MemorialExequialBeneficiary.contract_id == contract_id,
                MemorialExequialBeneficiary.organization_id == org_id,
            )
        )
        if ben is None:
            raise NotFoundError("Beneficiario no encontrado.")
        await db.delete(ben)
        await db.flush()

    @staticmethod
    async def _clear_titular(
        db: AsyncSession, org_id: uuid.UUID, contract_id: uuid.UUID,
    ) -> None:
        rows = await db.execute(
            select(MemorialExequialBeneficiary).where(
                MemorialExequialBeneficiary.contract_id == contract_id,
                MemorialExequialBeneficiary.organization_id == org_id,
                MemorialExequialBeneficiary.is_titular.is_(True),
            )
        )
        for b in rows.scalars().all():
            b.is_titular = False
        await db.flush()

    # ------------------------------------------------------------------
    # Coverage lookup — dado un documento, retorna contratos activos
    # ------------------------------------------------------------------
    @staticmethod
    async def coverage_by_document(
        db: AsyncSession,
        org_id: uuid.UUID,
        document_number: str,
    ) -> list[CoverageLookupResult]:
        doc = (document_number or "").strip()
        if not doc:
            return []
        rows = await db.execute(
            select(
                MemorialExequialBeneficiary,
                MemorialExequialContract,
                MemorialExequialPlan,
            )
            .join(
                MemorialExequialContract,
                MemorialExequialContract.id == MemorialExequialBeneficiary.contract_id,
            )
            .join(
                MemorialExequialPlan,
                MemorialExequialPlan.id == MemorialExequialContract.plan_id,
            )
            .where(
                MemorialExequialBeneficiary.organization_id == org_id,
                MemorialExequialBeneficiary.document_number == doc,
                MemorialExequialBeneficiary.removed_at.is_(None),
                MemorialExequialContract.status.in_(("active", "suspended")),
            )
        )
        out: list[CoverageLookupResult] = []
        for ben, contract, plan in rows.all():
            name = f"{ben.first_name} {ben.last_name or ''}".strip()
            out.append(CoverageLookupResult(
                contract_id=contract.id,
                contract_code=contract.code,
                plan_name=plan.name,
                plan_type=plan.plan_type,
                titular_display=_titular_display(contract),
                beneficiary_id=ben.id,
                beneficiary_name=name,
                beneficiary_relationship=ben.relationship_,
                is_titular=ben.is_titular,
                coverage_amount=Decimal(plan.coverage_amount),
                status=contract.status,
            ))
        return out
