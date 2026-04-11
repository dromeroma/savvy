"""SavvyEdu documents REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.edu.documents.schemas import (
    DocumentTemplateCreate,
    DocumentTemplateResponse,
    IssuedDocumentCreate,
    IssuedDocumentResponse,
)
from src.apps.edu.documents.service import EduDocumentService

router = APIRouter(prefix="/documents", tags=["Edu Documents"])


@router.get("/templates", response_model=list[DocumentTemplateResponse])
async def list_templates(
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduDocumentService.list_templates(db, org_id)


@router.post("/templates", response_model=DocumentTemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(
    data: DocumentTemplateCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduDocumentService.create_template(db, org_id, data)


@router.get("/issued", response_model=list[IssuedDocumentResponse])
async def list_issued(
    student_id: uuid.UUID | None = Query(None),
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduDocumentService.list_issued(db, org_id, student_id)


@router.post("/issue", response_model=IssuedDocumentResponse, status_code=status.HTTP_201_CREATED)
async def issue_document(
    data: IssuedDocumentCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    return await EduDocumentService.issue_document(db, org_id, data)
