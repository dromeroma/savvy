"""Endpoints REST de facturas — listado, detalle, generación, anulación, PDF."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.invoices.pdf import render_invoice_pdf
from src.apps.memorial.invoices.schemas import (
    BatchGenerateRequest,
    BatchGenerateResult,
    GenerateServiceInvoiceRequest,
    InvoiceListItem,
    InvoiceResponse,
)
from src.apps.memorial.invoices.service import InvoicesService
from src.core.dependencies import get_current_user, get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/invoices", tags=["Memorial · Facturas"])


def _user_uuid(user: dict[str, Any]) -> uuid.UUID:
    return uuid.UUID(user["sub"])


@router.get(
    "",
    response_model=list[InvoiceListItem],
    dependencies=[Depends(require_permission(
        "memorial", "invoices.read", "invoices.manage",
        "contracts.read", "contracts.manage",
    ))],
)
async def list_invoices(
    source_type: str | None = Query(None),
    status_: str | None = Query(None, alias="status"),
    contract_id: uuid.UUID | None = Query(None),
    service_id: uuid.UUID | None = Query(None),
    unpaid_only: bool = Query(False),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InvoicesService.list_invoices(
        db, org_id,
        source_type=source_type, status=status_,
        contract_id=contract_id, service_id=service_id,
        unpaid_only=unpaid_only, limit=limit, offset=offset,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    dependencies=[Depends(require_permission(
        "memorial", "invoices.read", "invoices.manage",
    ))],
)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InvoicesService.get_invoice(db, org_id, invoice_id)


@router.post(
    "/batch-generate-dues",
    response_model=BatchGenerateResult,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "invoices.manage"))],
)
async def batch_generate_dues(
    data: BatchGenerateRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await InvoicesService.batch_generate_dues(
        db, org_id, data, _user_uuid(user),
    )


@router.post(
    "/generate-for-service",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("memorial", "invoices.manage"))],
)
async def generate_for_service(
    data: GenerateServiceInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
    user: dict[str, Any] = Depends(get_current_user),
) -> Any:
    return await InvoicesService.generate_invoice_for_service(
        db, org_id, data, _user_uuid(user),
    )


@router.post(
    "/{invoice_id}/annul",
    response_model=InvoiceResponse,
    dependencies=[Depends(require_permission("memorial", "invoices.manage"))],
)
async def annul_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InvoicesService.annul_invoice(db, org_id, invoice_id)


@router.get(
    "/{invoice_id}/pdf",
    response_class=Response,
    dependencies=[Depends(require_permission(
        "memorial", "invoices.read", "invoices.manage",
    ))],
)
async def download_invoice_pdf(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Response:
    pdf_bytes, filename = await render_invoice_pdf(db, org_id, invoice_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
