"""CSV import endpoints for water subscribers and meters."""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Response, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.water.imports.schemas import (
    ImportCommitResponse,
    ImportPreviewResponse,
    MetersCommitRequest,
    SubscribersCommitRequest,
)
from src.apps.water.imports.service import ImportsService
from src.core.dependencies import get_db, get_org_id
from src.core.exceptions import ValidationError
from src.modules.apps.permissions import require_permission

router = APIRouter(prefix="/imports", tags=["Water · Importación"])


# ---------------------------------------------------------------- Subscribers


@router.post(
    "/subscribers/preview",
    response_model=ImportPreviewResponse,
    dependencies=[Depends(require_permission("water", "subscribers.manage"))],
)
async def preview_subscribers_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    raw = await file.read()
    if not raw:
        raise ValidationError("El archivo CSV está vacío.")
    try:
        return await ImportsService.preview_subscribers(db, org_id, raw)
    except ValueError as e:
        raise ValidationError(str(e)) from e


@router.post(
    "/subscribers/commit",
    response_model=ImportCommitResponse,
    dependencies=[Depends(require_permission("water", "subscribers.manage"))],
)
async def commit_subscribers_csv(
    data: SubscribersCommitRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ImportsService.commit_subscribers(db, org_id, data.rows)


@router.get(
    "/subscribers/template",
    response_class=Response,
    dependencies=[Depends(require_permission("water", "subscribers.manage"))],
)
async def subscribers_template() -> Response:
    csv_text = ImportsService.subscribers_template()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="suscriptores-plantilla.csv"'},
    )


# ---------------------------------------------------------------- Meters


@router.post(
    "/meters/preview",
    response_model=ImportPreviewResponse,
    dependencies=[Depends(require_permission("water", "meters.manage"))],
)
async def preview_meters_csv(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    raw = await file.read()
    if not raw:
        raise ValidationError("El archivo CSV está vacío.")
    try:
        return await ImportsService.preview_meters(db, org_id, raw)
    except ValueError as e:
        raise ValidationError(str(e)) from e


@router.post(
    "/meters/commit",
    response_model=ImportCommitResponse,
    dependencies=[Depends(require_permission("water", "meters.manage"))],
)
async def commit_meters_csv(
    data: MetersCommitRequest,
    db: AsyncSession = Depends(get_db),
    org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await ImportsService.commit_meters(db, org_id, data.rows)


@router.get(
    "/meters/template",
    response_class=Response,
    dependencies=[Depends(require_permission("water", "meters.manage"))],
)
async def meters_template() -> Response:
    csv_text = ImportsService.meters_template()
    return Response(
        content=csv_text,
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="medidores-plantilla.csv"'},
    )
