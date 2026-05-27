"""Lógica del portal cliente: autenticación por (org + email/doc) y vistas
de solo lectura sobre el contrato del titular."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from jose import JWTError, jwt
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.models import (
    MemorialExequialBeneficiary,
    MemorialExequialContract,
    MemorialExequialPlan,
    MemorialInvoice,
    MemorialPayment,
    MemorialPaymentInvoice,
    MemorialService,
)
from src.apps.memorial.portal.schemas import (
    PortalAuthRequest,
    PortalBeneficiary,
    PortalContract,
)
from src.core.config import get_settings
from src.core.exceptions import NotFoundError, UnauthorizedError
from src.modules.organization.models import Organization

settings = get_settings()

PORTAL_TOKEN_TTL_HOURS = 24
PORTAL_TOKEN_SCOPE = "memorial_portal"


def issue_portal_token(contract_id: uuid.UUID, org_id: uuid.UUID) -> tuple[str, int]:
    """Genera un JWT scope:portal — corto, sin tipo 'access', con contract+org."""
    ttl = timedelta(hours=PORTAL_TOKEN_TTL_HOURS)
    expire = datetime.now(UTC) + ttl
    payload = {
        "scope": PORTAL_TOKEN_SCOPE,
        "contract_id": str(contract_id),
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
        raise UnauthorizedError("Token de portal inválido o expirado.") from exc
    if payload.get("scope") != PORTAL_TOKEN_SCOPE:
        raise UnauthorizedError("Token con alcance inválido para portal.")
    return payload


async def authenticate_portal(
    db: AsyncSession, data: PortalAuthRequest
) -> tuple[str, int, MemorialExequialContract, Organization]:
    """Busca org+contrato por slug + (email o documento) del titular."""
    if not data.email and not data.document_number:
        raise UnauthorizedError("Debe ingresar email o número de documento.")

    org = await db.scalar(
        select(Organization).where(Organization.slug == data.org_slug)
    )
    if org is None:
        raise UnauthorizedError("Organización no encontrada.")

    filters = [MemorialExequialContract.organization_id == org.id]
    or_filters = []
    if data.email:
        or_filters.append(MemorialExequialContract.titular_email == str(data.email))
    if data.document_number:
        or_filters.append(MemorialExequialContract.titular_document_number == data.document_number)
    filters.append(or_(*or_filters))

    contract = await db.scalar(
        select(MemorialExequialContract).where(and_(*filters)).limit(1)
    )
    if contract is None:
        raise UnauthorizedError("Credenciales no válidas. Verifique sus datos.")

    token, ttl = issue_portal_token(contract.id, org.id)
    return token, ttl, contract, org


async def load_portal_contract(
    db: AsyncSession, contract_id: uuid.UUID, org_id: uuid.UUID
) -> PortalContract:
    contract = await db.scalar(
        select(MemorialExequialContract).where(
            MemorialExequialContract.id == contract_id,
            MemorialExequialContract.organization_id == org_id,
        )
    )
    if contract is None:
        raise NotFoundError("Contrato no encontrado.")

    plan = await db.scalar(
        select(MemorialExequialPlan).where(MemorialExequialPlan.id == contract.plan_id)
    )
    org = await db.scalar(select(Organization).where(Organization.id == org_id))

    benes_rows = await db.execute(
        select(MemorialExequialBeneficiary)
        .where(MemorialExequialBeneficiary.contract_id == contract.id)
        .order_by(MemorialExequialBeneficiary.is_titular.desc(), MemorialExequialBeneficiary.joined_at)
    )
    beneficiaries: list[PortalBeneficiary] = []
    for b in benes_rows.scalars().all():
        beneficiaries.append(PortalBeneficiary(
            id=b.id,
            first_name=b.first_name,
            last_name=b.last_name,
            document_number=b.document_number,
            relationship=b.relationship_,
            is_titular=b.is_titular,
            joined_at=b.joined_at,
        ))

    return PortalContract(
        id=contract.id,
        code=contract.code,
        plan_name=plan.name if plan else "—",
        plan_code=plan.code if plan else "—",
        affiliate_type=contract.affiliate_type,  # type: ignore[arg-type]
        titular_first_name=contract.titular_first_name,
        titular_last_name=contract.titular_last_name,
        titular_business_name=contract.titular_business_name,
        titular_email=contract.titular_email,
        titular_phone=contract.titular_phone,
        titular_mobile=contract.titular_mobile,
        titular_address=contract.titular_address,
        payment_frequency=contract.payment_frequency,  # type: ignore[arg-type]
        fee_amount=contract.fee_amount,
        start_date=contract.start_date,
        next_payment_date=contract.next_payment_date,
        status=contract.status,  # type: ignore[arg-type]
        beneficiaries=beneficiaries,
        organization_name=org.name if org else "—",
    )


async def list_portal_invoices(
    db: AsyncSession, contract_id: uuid.UUID, org_id: uuid.UUID
) -> list[MemorialInvoice]:
    rows = await db.execute(
        select(MemorialInvoice)
        .where(
            MemorialInvoice.organization_id == org_id,
            MemorialInvoice.contract_id == contract_id,
        )
        .order_by(MemorialInvoice.issue_date.desc())
    )
    return list(rows.scalars().all())


async def list_portal_payments(
    db: AsyncSession, contract_id: uuid.UUID, org_id: uuid.UUID
) -> list[MemorialPayment]:
    rows = await db.execute(
        select(MemorialPayment)
        .where(
            MemorialPayment.organization_id == org_id,
            MemorialPayment.contract_id == contract_id,
        )
        .order_by(MemorialPayment.payment_date.desc())
    )
    return list(rows.scalars().all())


async def list_portal_services(
    db: AsyncSession,
    contract_id: uuid.UUID,
    org_id: uuid.UUID,
) -> list[MemorialService]:
    """Servicios cubiertos por este contrato exequial (link directo)."""
    rows = await db.execute(
        select(MemorialService)
        .where(
            MemorialService.organization_id == org_id,
            MemorialService.exequial_contract_id == contract_id,
        )
        .order_by(MemorialService.deceased_death_date.desc())
    )
    return list(rows.scalars().all())


async def get_portal_invoice(
    db: AsyncSession,
    contract_id: uuid.UUID,
    org_id: uuid.UUID,
    invoice_id: uuid.UUID,
) -> MemorialInvoice:
    inv = await db.scalar(
        select(MemorialInvoice).where(
            MemorialInvoice.id == invoice_id,
            MemorialInvoice.organization_id == org_id,
            MemorialInvoice.contract_id == contract_id,
        )
    )
    if inv is None:
        raise NotFoundError("Factura no encontrada.")
    return inv
