"""SavvyCRM contacts and companies REST endpoints."""

import uuid
from typing import Any

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.dependencies import get_db, get_org_id
from src.apps.crm.contacts.schemas import *
from src.apps.crm.contacts.service import CompanyService, ContactService

router = APIRouter(tags=["CRM Contacts"])

# Contacts
@router.get("/contacts", response_model=dict)
async def list_contacts(
    search: str | None = Query(None), lifecycle: str | None = Query(None),
    page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id),
) -> Any:
    items, total = await ContactService.list_contacts(db, org_id, search, lifecycle, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.post("/contacts", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def create_contact(data: ContactCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ContactService.create_contact(db, org_id, data)

@router.get("/contacts/{contact_id}", response_model=ContactResponse)
async def get_contact(contact_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ContactService.get_contact(db, org_id, contact_id)

@router.patch("/contacts/{contact_id}", response_model=ContactResponse)
async def update_contact(contact_id: uuid.UUID, data: ContactUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await ContactService.update_contact(db, org_id, contact_id, data)

# Companies
@router.get("/companies", response_model=list[CompanyResponse])
async def list_companies(search: str | None = Query(None), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CompanyService.list_companies(db, org_id, search)

@router.post("/companies", response_model=CompanyResponse, status_code=status.HTTP_201_CREATED)
async def create_company(data: CompanyCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CompanyService.create_company(db, org_id, data)

@router.patch("/companies/{company_id}", response_model=CompanyResponse)
async def update_company(company_id: uuid.UUID, data: CompanyUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CompanyService.update_company(db, org_id, company_id, data)
