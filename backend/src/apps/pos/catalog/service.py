"""Business logic for POS catalog."""

from __future__ import annotations
import uuid
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError
from src.apps.pos.catalog.models import PosCategory, PosLocation, PosProduct, PosProductVariant
from src.apps.pos.catalog.schemas import CategoryCreate, LocationCreate, ProductCreate, ProductUpdate


class CatalogService:

    # Locations
    @staticmethod
    async def list_locations(db: AsyncSession, org_id: uuid.UUID) -> list[PosLocation]:
        return list((await db.execute(select(PosLocation).where(PosLocation.organization_id == org_id).order_by(PosLocation.name))).scalars().all())

    @staticmethod
    async def create_location(db: AsyncSession, org_id: uuid.UUID, data: LocationCreate) -> PosLocation:
        loc = PosLocation(organization_id=org_id, **data.model_dump())
        db.add(loc); await db.flush(); await db.refresh(loc); return loc

    # Categories
    @staticmethod
    async def list_categories(db: AsyncSession, org_id: uuid.UUID) -> list[PosCategory]:
        return list((await db.execute(select(PosCategory).where(PosCategory.organization_id == org_id).order_by(PosCategory.sort_order, PosCategory.name))).scalars().all())

    @staticmethod
    async def create_category(db: AsyncSession, org_id: uuid.UUID, data: CategoryCreate) -> PosCategory:
        cat = PosCategory(organization_id=org_id, **data.model_dump())
        db.add(cat); await db.flush(); await db.refresh(cat); return cat

    # Products
    @staticmethod
    async def list_products(
        db: AsyncSession, org_id: uuid.UUID, search: str | None = None,
        category_id: uuid.UUID | None = None, page: int = 1, page_size: int = 50,
    ) -> tuple[list[PosProduct], int]:
        q = select(PosProduct).where(PosProduct.organization_id == org_id)
        if category_id: q = q.where(PosProduct.category_id == category_id)
        if search:
            t = f"%{search}%"
            q = q.where(or_(PosProduct.name.ilike(t), PosProduct.sku.ilike(t), PosProduct.barcode.ilike(t)))
        count_result = await db.execute(select(func.count()).select_from(q.subquery()))
        total = count_result.scalar() or 0
        result = await db.execute(q.order_by(PosProduct.name).offset((page - 1) * page_size).limit(page_size))
        return list(result.scalars().all()), total

    @staticmethod
    async def create_product(db: AsyncSession, org_id: uuid.UUID, data: ProductCreate) -> PosProduct:
        product = PosProduct(
            organization_id=org_id, category_id=data.category_id,
            sku=data.sku, barcode=data.barcode, name=data.name, description=data.description,
            product_type=data.product_type, price=data.price, cost=data.cost,
            tax_id=data.tax_id, tracks_inventory=data.tracks_inventory, image_url=data.image_url,
        )
        db.add(product)
        await db.flush()
        for v in data.variants:
            variant = PosProductVariant(product_id=product.id, **v.model_dump())
            db.add(variant)
        await db.flush()
        await db.refresh(product)
        return product

    @staticmethod
    async def get_product(db: AsyncSession, org_id: uuid.UUID, product_id: uuid.UUID) -> PosProduct:
        result = await db.execute(select(PosProduct).where(PosProduct.id == product_id, PosProduct.organization_id == org_id))
        p = result.scalar_one_or_none()
        if p is None: raise NotFoundError("Product not found.")
        return p

    @staticmethod
    async def update_product(db: AsyncSession, org_id: uuid.UUID, product_id: uuid.UUID, data: ProductUpdate) -> PosProduct:
        p = await CatalogService.get_product(db, org_id, product_id)
        for f, v in data.model_dump(exclude_unset=True).items(): setattr(p, f, v)
        await db.flush(); await db.refresh(p); return p

    @staticmethod
    async def find_by_barcode(db: AsyncSession, org_id: uuid.UUID, barcode: str) -> PosProduct | None:
        result = await db.execute(select(PosProduct).where(PosProduct.organization_id == org_id, PosProduct.barcode == barcode))
        return result.scalar_one_or_none()
