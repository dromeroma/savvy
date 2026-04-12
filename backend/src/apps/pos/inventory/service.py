"""Business logic for POS inventory — stock tracking with audit trail."""

from __future__ import annotations
import uuid
from decimal import Decimal
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.core.exceptions import NotFoundError, ValidationError
from src.apps.pos.inventory.models import PosInventory, PosStockMovement
from src.apps.pos.inventory.schemas import InventoryAdjustment


class InventoryService:

    @staticmethod
    async def get_stock(
        db: AsyncSession, org_id: uuid.UUID,
        product_id: uuid.UUID, location_id: uuid.UUID,
        variant_id: uuid.UUID | None = None,
    ) -> PosInventory | None:
        q = select(PosInventory).where(
            PosInventory.organization_id == org_id,
            PosInventory.product_id == product_id,
            PosInventory.location_id == location_id,
        )
        if variant_id:
            q = q.where(PosInventory.variant_id == variant_id)
        else:
            q = q.where(PosInventory.variant_id.is_(None))
        return (await db.execute(q)).scalar_one_or_none()

    @staticmethod
    async def record_movement(
        db: AsyncSession, org_id: uuid.UUID, data: InventoryAdjustment,
        reference_type: str | None = None, reference_id: uuid.UUID | None = None,
    ) -> PosStockMovement:
        """Record a stock movement AND update materialized inventory level."""
        # Get or create inventory record
        inv = await InventoryService.get_stock(db, org_id, data.product_id, data.location_id, data.variant_id)
        if inv is None:
            inv = PosInventory(
                organization_id=org_id,
                product_id=data.product_id, variant_id=data.variant_id,
                location_id=data.location_id, quantity=0,
            )
            db.add(inv)
            await db.flush()

        # Validate no negative stock for sales
        new_qty = Decimal(str(inv.quantity)) + Decimal(str(data.quantity))
        if new_qty < 0 and data.movement_type == "sale":
            raise ValidationError(f"Insufficient stock: current={inv.quantity}, requested={abs(data.quantity)}")

        # Record immutable movement
        movement = PosStockMovement(
            organization_id=org_id,
            product_id=data.product_id, variant_id=data.variant_id,
            location_id=data.location_id, movement_type=data.movement_type,
            quantity=data.quantity, unit_cost=data.unit_cost,
            reference_type=reference_type, reference_id=reference_id,
            notes=data.notes,
        )
        db.add(movement)

        # Update materialized view
        inv.quantity = float(new_qty)

        await db.flush()
        await db.refresh(movement)
        return movement

    @staticmethod
    async def list_inventory(
        db: AsyncSession, org_id: uuid.UUID, location_id: uuid.UUID | None = None,
    ) -> list[PosInventory]:
        q = select(PosInventory).where(PosInventory.organization_id == org_id)
        if location_id: q = q.where(PosInventory.location_id == location_id)
        return list((await db.execute(q)).scalars().all())

    @staticmethod
    async def list_movements(
        db: AsyncSession, org_id: uuid.UUID, product_id: uuid.UUID | None = None, limit: int = 100,
    ) -> list[PosStockMovement]:
        q = select(PosStockMovement).where(PosStockMovement.organization_id == org_id)
        if product_id: q = q.where(PosStockMovement.product_id == product_id)
        return list((await db.execute(q.order_by(PosStockMovement.created_at.desc()).limit(limit))).scalars().all())
