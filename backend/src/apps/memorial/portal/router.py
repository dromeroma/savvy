"""Portal del cliente — endpoints públicos (autenticados con JWT scope:portal)."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Response
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.invoices.pdf import render_invoice_pdf
from src.apps.memorial.portal.schemas import (
    PortalAuthRequest,
    PortalAuthResponse,
    PortalContract,
    PortalInvoiceItem,
    PortalPaymentItem,
    PortalServiceItem,
)
from src.apps.memorial.portal.service import (
    authenticate_portal,
    decode_portal_token,
    get_portal_invoice,
    list_portal_invoices,
    list_portal_payments,
    list_portal_services,
    load_portal_contract,
)
from src.core.dependencies import get_db
from src.core.exceptions import UnauthorizedError

router = APIRouter(prefix="/memorial-portal", tags=["Memorial · Portal cliente"])
bearer = HTTPBearer(auto_error=False)


async def _portal_payload(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer),
) -> dict[str, Any]:
    if credentials is None:
        raise UnauthorizedError("Token de portal requerido.")
    return decode_portal_token(credentials.credentials)


def _portal_ctx(payload: dict[str, Any]) -> tuple[uuid.UUID, uuid.UUID]:
    contract_id = uuid.UUID(payload["contract_id"])
    org_id = uuid.UUID(payload["org_id"])
    return contract_id, org_id


@router.post("/auth", response_model=PortalAuthResponse)
async def portal_auth(
    data: PortalAuthRequest,
    db: AsyncSession = Depends(get_db),
) -> PortalAuthResponse:
    token, ttl, contract, org = await authenticate_portal(db, data)
    portal_contract = await load_portal_contract(db, contract.id, org.id)
    return PortalAuthResponse(
        token=token,
        expires_in_seconds=ttl,
        contract=portal_contract,
    )


@router.get("/me", response_model=PortalContract)
async def portal_me(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> PortalContract:
    contract_id, org_id = _portal_ctx(payload)
    return await load_portal_contract(db, contract_id, org_id)


@router.get("/invoices", response_model=list[PortalInvoiceItem])
async def portal_invoices(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    contract_id, org_id = _portal_ctx(payload)
    return await list_portal_invoices(db, contract_id, org_id)


@router.get("/payments", response_model=list[PortalPaymentItem])
async def portal_payments(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    contract_id, org_id = _portal_ctx(payload)
    return await list_portal_payments(db, contract_id, org_id)


@router.get("/services", response_model=list[PortalServiceItem])
async def portal_services(
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Any:
    contract_id, org_id = _portal_ctx(payload)
    return await list_portal_services(db, contract_id, org_id)


@router.get("/invoices/{invoice_id}/pdf")
async def portal_invoice_pdf(
    invoice_id: uuid.UUID,
    payload: dict[str, Any] = Depends(_portal_payload),
    db: AsyncSession = Depends(get_db),
) -> Response:
    contract_id, org_id = _portal_ctx(payload)
    await get_portal_invoice(db, contract_id, org_id, invoice_id)
    pdf_bytes, filename = await render_invoice_pdf(db, org_id, invoice_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
