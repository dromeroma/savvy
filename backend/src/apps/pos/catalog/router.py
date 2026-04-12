"""POS catalog REST endpoints."""

import uuid
from typing import Any
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.dependencies import get_db, get_org_id
from src.apps.pos.catalog.schemas import *
from src.apps.pos.catalog.service import CatalogService

router = APIRouter(tags=["POS Catalog"])

@router.get("/locations", response_model=list[LocationResponse])
async def list_locations(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CatalogService.list_locations(db, org_id)

@router.post("/locations", response_model=LocationResponse, status_code=status.HTTP_201_CREATED)
async def create_location(data: LocationCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CatalogService.create_location(db, org_id, data)

@router.get("/categories", response_model=list[CategoryResponse])
async def list_categories(db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CatalogService.list_categories(db, org_id)

@router.post("/categories", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(data: CategoryCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CatalogService.create_category(db, org_id, data)

@router.get("/products", response_model=dict)
async def list_products(search: str | None = Query(None), category_id: uuid.UUID | None = Query(None), page: int = Query(1, ge=1), page_size: int = Query(50, ge=1, le=200), db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    items, total = await CatalogService.list_products(db, org_id, search, category_id, page, page_size)
    return {"items": items, "total": total, "page": page, "page_size": page_size}

@router.post("/products", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(data: ProductCreate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CatalogService.create_product(db, org_id, data)

@router.get("/products/{product_id}", response_model=ProductResponse)
async def get_product(product_id: uuid.UUID, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CatalogService.get_product(db, org_id, product_id)

@router.patch("/products/{product_id}", response_model=ProductResponse)
async def update_product(product_id: uuid.UUID, data: ProductUpdate, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    return await CatalogService.update_product(db, org_id, product_id, data)

@router.get("/products/barcode/{barcode}", response_model=ProductResponse)
async def find_by_barcode(barcode: str, db: AsyncSession = Depends(get_db), org_id: uuid.UUID = Depends(get_org_id)) -> Any:
    from src.core.exceptions import NotFoundError
    p = await CatalogService.find_by_barcode(db, org_id, barcode)
    if p is None: raise NotFoundError("Product not found.")
    return p
