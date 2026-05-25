"""Invoices REST endpoints."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.invoices.pdf import render_invoice_pdf
from src.apps.water.invoices.schemas import (
    BatchGenerateRequest,
    BatchGenerateResult,
    GenerateInvoiceRequest,
    InvoiceListItem,
    InvoiceResponse,
)
from src.apps.water.invoices.service import InvoicesService
from src.core.dependencies import get_db, get_org_id
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/invoices", tags=["Water · Facturación"])


@router.get(
    "",
    response_model=list[InvoiceListItem],
    dependencies=[Depends(require_permission("water", "invoices.read", "invoices.manage"))],
)
async def list_invoices(
    status_: str | None = Query(None, alias="status"),
    period_year: int | None = Query(None),
    period_month: int | None = Query(None, ge=1, le=12),
    subscriber_id: uuid.UUID | None = Query(None),
    unpaid_only: bool = Query(False),
    limit: int = Query(200, ge=1, le=500),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InvoicesService.list_invoices(
        db, org_id, status=status_, period_year=period_year,
        period_month=period_month, subscriber_id=subscriber_id,
        unpaid_only=unpaid_only, limit=limit, offset=offset,
    )


@router.get(
    "/{invoice_id}",
    response_model=InvoiceResponse,
    dependencies=[Depends(require_permission("water", "invoices.read", "invoices.manage"))],
)
async def get_invoice(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InvoicesService.get_invoice(db, org_id, invoice_id)


@router.post(
    "/generate",
    response_model=InvoiceResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "invoices.manage"))],
)
async def generate_invoice(
    data: GenerateInvoiceRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InvoicesService.generate_from_consumption(db, org_id, data)


@router.post(
    "/batch-generate",
    response_model=BatchGenerateResult,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_permission("water", "invoices.manage"))],
)
async def batch_generate(
    data: BatchGenerateRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await InvoicesService.batch_generate(db, org_id, data)


@router.post(
    "/{invoice_id}/annul",
    response_model=InvoiceResponse,
    dependencies=[Depends(require_permission("water", "invoices.manage"))],
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
    dependencies=[Depends(require_permission("water", "invoices.read", "invoices.manage"))],
)
async def download_invoice_pdf(
    invoice_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Response:
    """Render the invoice as a PDF document."""
    pdf_bytes, filename = await render_invoice_pdf(db, org_id, invoice_id)
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="{filename}"'},
    )
