"""Business logic for POS sales — integrates with SavvyPay and inventory."""

from __future__ import annotations
import uuid
from decimal import Decimal, ROUND_HALF_UP
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError, ValidationError
from src.apps.pos.sales.models import PosSale, PosSaleLine
from src.apps.pos.sales.schemas import SaleCreate
from src.apps.pos.catalog.models import PosProduct, PosProductVariant
from src.apps.pos.inventory.service import InventoryService
from src.apps.pos.inventory.schemas import InventoryAdjustment


def _d(v): return Decimal(str(v)) if v else Decimal("0")
def _r2(v: Decimal) -> float: return float(v.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


class SalesService:

    @staticmethod
    async def _next_sale_number(db: AsyncSession, org_id: uuid.UUID) -> str:
        result = await db.execute(select(func.count()).where(PosSale.organization_id == org_id))
        count = (result.scalar() or 0) + 1
        return f"SALE-{count:06d}"

    @staticmethod
    async def create_sale(db: AsyncSession, org_id: uuid.UUID, data: SaleCreate) -> PosSale:
        """Create a sale with automatic inventory deduction and payment tracking."""
        sale_number = await SalesService._next_sale_number(db, org_id)

        subtotal = Decimal("0")
        total_discount = Decimal("0")
        total_tax = Decimal("0")
        line_objects = []

        for line in data.lines:
            # Get product
            product_result = await db.execute(
                select(PosProduct).where(PosProduct.id == line.product_id, PosProduct.organization_id == org_id)
            )
            product = product_result.scalar_one_or_none()
            if product is None:
                raise NotFoundError(f"Product {line.product_id} not found.")

            unit_price = _d(line.unit_price) if line.unit_price is not None else _d(product.price)

            # Get variant price if applicable
            if line.variant_id:
                v_result = await db.execute(select(PosProductVariant).where(PosProductVariant.id == line.variant_id))
                variant = v_result.scalar_one_or_none()
                if variant and variant.price_override is not None:
                    unit_price = _d(variant.price_override)

            qty = _d(line.quantity)
            discount = _d(line.discount)
            gross = unit_price * qty
            net = gross - discount
            line_total = _r2(net)

            subtotal += gross
            total_discount += discount

            sale_line = PosSaleLine(
                product_id=line.product_id, variant_id=line.variant_id,
                product_name=product.name, sku=product.sku,
                quantity=line.quantity, unit_price=float(unit_price),
                discount=float(discount), tax_rate=0, tax_amount=0, line_total=line_total,
            )
            line_objects.append((sale_line, product, qty))

        total = subtotal - total_discount + total_tax

        sale = PosSale(
            organization_id=org_id,
            sale_number=sale_number,
            location_id=data.location_id,
            register_id=data.register_id,
            customer_person_id=data.customer_person_id,
            subtotal=_r2(subtotal),
            discount_amount=_r2(total_discount),
            tax_amount=_r2(total_tax),
            total=_r2(total),
            payment_method=data.payment_method,
            payment_details=data.payment_details,
            notes=data.notes,
            status="completed",
        )
        db.add(sale)
        await db.flush()

        # Add lines
        for sale_line, product, qty in line_objects:
            sale_line.sale_id = sale.id
            db.add(sale_line)

        await db.flush()

        # Deduct inventory for each line
        for sale_line, product, qty in line_objects:
            if product.tracks_inventory:
                await InventoryService.record_movement(
                    db, org_id,
                    InventoryAdjustment(
                        product_id=product.id, variant_id=sale_line.variant_id,
                        location_id=data.location_id,
                        quantity=-float(qty),  # Negative = out
                        movement_type="sale",
                        unit_cost=float(product.cost),
                    ),
                    reference_type="pos_sale", reference_id=sale.id,
                )

        await db.refresh(sale)
        return sale

    @staticmethod
    async def list_sales(
        db: AsyncSession, org_id: uuid.UUID,
        location_id: uuid.UUID | None = None, status_filter: str | None = None, limit: int = 50,
    ) -> list[PosSale]:
        q = select(PosSale).where(PosSale.organization_id == org_id)
        if location_id: q = q.where(PosSale.location_id == location_id)
        if status_filter: q = q.where(PosSale.status == status_filter)
        return list((await db.execute(q.order_by(PosSale.created_at.desc()).limit(limit))).scalars().all())

    @staticmethod
    async def get_sale(db: AsyncSession, org_id: uuid.UUID, sale_id: uuid.UUID) -> PosSale:
        result = await db.execute(select(PosSale).where(PosSale.id == sale_id, PosSale.organization_id == org_id))
        sale = result.scalar_one_or_none()
        if sale is None: raise NotFoundError("Sale not found.")
        return sale

    @staticmethod
    async def void_sale(db: AsyncSession, org_id: uuid.UUID, sale_id: uuid.UUID) -> PosSale:
        sale = await SalesService.get_sale(db, org_id, sale_id)
        if sale.status != "completed":
            raise ValidationError("Only completed sales can be voided.")
        sale.status = "voided"

        # Reverse inventory movements
        for line in sale.lines:
            await InventoryService.record_movement(
                db, org_id,
                InventoryAdjustment(
                    product_id=line.product_id, variant_id=line.variant_id,
                    location_id=sale.location_id,
                    quantity=float(line.quantity),  # Positive = return to stock
                    movement_type="return",
                ),
                reference_type="pos_sale_void", reference_id=sale.id,
            )

        await db.flush()
        await db.refresh(sale)
        return sale
