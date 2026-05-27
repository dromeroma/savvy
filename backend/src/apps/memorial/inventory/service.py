"""Lógica de inventario: items + movimientos con stock recalculado."""

from __future__ import annotations

import uuid
from datetime import date
from decimal import Decimal

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.apps.memorial.inventory.schemas import (
    ItemCreate,
    ItemListItem,
    ItemUpdate,
    MovementCreate,
)
from src.apps.memorial.models import (
    MemorialInventoryItem,
    MemorialInventoryMovement,
)
from src.core.exceptions import ConflictError, NotFoundError, ValidationError


# Tipos que SUMAN al stock vs los que RESTAN.
ENTRY_TYPES = {"entry", "transfer_in"}
EXIT_TYPES = {"exit", "transfer_out"}


class InventoryService:

    # ------------------------------------------------------------------
    # Items
    # ------------------------------------------------------------------
    @staticmethod
    async def list_items(
        db: AsyncSession,
        org_id: uuid.UUID,
        category: str | None = None,
        active_only: bool = False,
        low_stock_only: bool = False,
        search: str | None = None,
    ) -> list[ItemListItem]:
        stmt = (
            select(MemorialInventoryItem)
            .where(MemorialInventoryItem.organization_id == org_id)
            .order_by(MemorialInventoryItem.category, MemorialInventoryItem.code)
        )
        if category:
            stmt = stmt.where(MemorialInventoryItem.category == category)
        if active_only:
            stmt = stmt.where(MemorialInventoryItem.is_active.is_(True))
        if search:
            like = f"%{search.lower()}%"
            stmt = stmt.where(
                or_(
                    func.lower(MemorialInventoryItem.code).like(like),
                    func.lower(MemorialInventoryItem.name).like(like),
                )
            )
        rows = await db.execute(stmt)
        items = list(rows.scalars().all())
        out: list[ItemListItem] = []
        for i in items:
            is_low = Decimal(i.current_stock) <= Decimal(i.min_stock)
            if low_stock_only and not is_low:
                continue
            out.append(ItemListItem(
                id=i.id, code=i.code, name=i.name, category=i.category,
                unit=i.unit, current_stock=i.current_stock,
                min_stock=i.min_stock, max_stock=i.max_stock,
                unit_cost=i.unit_cost, sale_price=i.sale_price,
                is_active=i.is_active, is_low_stock=is_low,
            ))
        return out

    @staticmethod
    async def get_item(
        db: AsyncSession, org_id: uuid.UUID, item_id: uuid.UUID,
    ) -> MemorialInventoryItem:
        item = await db.scalar(
            select(MemorialInventoryItem).where(
                MemorialInventoryItem.id == item_id,
                MemorialInventoryItem.organization_id == org_id,
            )
        )
        if item is None:
            raise NotFoundError("Item de inventario no encontrado.")
        return item

    @staticmethod
    async def create_item(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: ItemCreate,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialInventoryItem:
        existing = await db.scalar(
            select(MemorialInventoryItem).where(
                MemorialInventoryItem.organization_id == org_id,
                MemorialInventoryItem.code == data.code,
            )
        )
        if existing is not None:
            raise ConflictError(f"Ya existe un item con código '{data.code}'.")

        payload = data.model_dump(exclude={"initial_stock"})
        item = MemorialInventoryItem(
            organization_id=org_id,
            current_stock=Decimal("0"),
            **payload,
        )
        db.add(item)
        await db.flush()

        # Si vino stock inicial > 0, registrar movimiento de entrada
        if data.initial_stock and data.initial_stock > 0:
            await InventoryService._record_movement_internal(
                db, org_id, item,
                MovementCreate(
                    item_id=item.id,
                    movement_type="entry",
                    quantity=data.initial_stock,
                    unit_cost=data.unit_cost,
                    reason="stock_inicial",
                ),
                actor_user_id,
            )

        await db.refresh(item)
        return item

    @staticmethod
    async def update_item(
        db: AsyncSession,
        org_id: uuid.UUID,
        item_id: uuid.UUID,
        data: ItemUpdate,
    ) -> MemorialInventoryItem:
        item = await InventoryService.get_item(db, org_id, item_id)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(item, k, v)
        await db.flush()
        await db.refresh(item)
        return item

    @staticmethod
    async def delete_item(
        db: AsyncSession, org_id: uuid.UUID, item_id: uuid.UUID,
    ) -> None:
        # Bloqueamos si tiene movimientos (preserva historial)
        in_use = await db.scalar(
            select(func.count(MemorialInventoryMovement.id)).where(
                MemorialInventoryMovement.item_id == item_id,
            )
        )
        if int(in_use or 0) > 0:
            raise ConflictError(
                "Item con movimientos en el historial — desactívalo en vez de eliminarlo.",
            )
        item = await InventoryService.get_item(db, org_id, item_id)
        await db.delete(item)
        await db.flush()

    # ------------------------------------------------------------------
    # Movements
    # ------------------------------------------------------------------
    @staticmethod
    async def _next_consecutive(db: AsyncSession, org_id: uuid.UUID) -> int:
        last = await db.scalar(
            select(func.coalesce(func.max(MemorialInventoryMovement.consecutive), 0))
            .where(MemorialInventoryMovement.organization_id == org_id)
        )
        return int(last) + 1

    @staticmethod
    async def record_movement(
        db: AsyncSession,
        org_id: uuid.UUID,
        data: MovementCreate,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialInventoryMovement:
        item = await InventoryService.get_item(db, org_id, data.item_id)
        return await InventoryService._record_movement_internal(
            db, org_id, item, data, actor_user_id,
        )

    @staticmethod
    async def _record_movement_internal(
        db: AsyncSession,
        org_id: uuid.UUID,
        item: MemorialInventoryItem,
        data: MovementCreate,
        actor_user_id: uuid.UUID | None,
    ) -> MemorialInventoryMovement:
        qty = Decimal(data.quantity)
        current = Decimal(item.current_stock)
        mtype = data.movement_type

        if mtype in ENTRY_TYPES:
            new_stock = current + qty
        elif mtype in EXIT_TYPES:
            if qty > current:
                raise ValidationError(
                    f"No hay stock suficiente para retirar {qty} de '{item.code}' "
                    f"(disponible: {current}).",
                )
            new_stock = current - qty
        elif mtype == "adjustment":
            # Ajuste: la qty se interpreta como el nuevo valor absoluto
            new_stock = qty
        else:
            raise ValidationError(f"Tipo de movimiento inválido: {mtype}")

        consec = await InventoryService._next_consecutive(db, org_id)
        movement = MemorialInventoryMovement(
            organization_id=org_id,
            consecutive=consec,
            code=f"MOV-{consec:04d}",
            item_id=item.id,
            movement_type=mtype,
            quantity=qty,
            unit_cost=data.unit_cost,
            reason=data.reason,
            reference_doc=data.reference_doc,
            supplier=data.supplier,
            service_id=data.service_id,
            movement_date=data.movement_date or date.today(),
            notes=data.notes,
            recorded_by=actor_user_id,
        )
        item.current_stock = new_stock
        if mtype == "entry" and data.unit_cost is not None and data.unit_cost > 0:
            # Actualizar costo unitario al último de compra
            item.unit_cost = data.unit_cost
        db.add(movement)
        await db.flush()
        return movement

    @staticmethod
    async def list_movements(
        db: AsyncSession,
        org_id: uuid.UUID,
        item_id: uuid.UUID | None = None,
        movement_type: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        limit: int = 200,
        offset: int = 0,
    ):
        stmt = (
            select(
                MemorialInventoryMovement.id,
                MemorialInventoryMovement.code,
                MemorialInventoryMovement.consecutive,
                MemorialInventoryMovement.item_id,
                MemorialInventoryItem.code.label("item_code"),
                MemorialInventoryItem.name.label("item_name"),
                MemorialInventoryMovement.movement_type,
                MemorialInventoryMovement.quantity,
                MemorialInventoryMovement.unit_cost,
                MemorialInventoryMovement.reason,
                MemorialInventoryMovement.movement_date,
                MemorialInventoryMovement.created_at,
            )
            .join(
                MemorialInventoryItem,
                MemorialInventoryItem.id == MemorialInventoryMovement.item_id,
            )
            .where(MemorialInventoryMovement.organization_id == org_id)
            .order_by(MemorialInventoryMovement.consecutive.desc())
            .limit(limit).offset(offset)
        )
        if item_id:
            stmt = stmt.where(MemorialInventoryMovement.item_id == item_id)
        if movement_type:
            stmt = stmt.where(MemorialInventoryMovement.movement_type == movement_type)
        if date_from:
            stmt = stmt.where(MemorialInventoryMovement.movement_date >= date_from)
        if date_to:
            stmt = stmt.where(MemorialInventoryMovement.movement_date <= date_to)
        rows = await db.execute(stmt)
        from src.apps.memorial.inventory.schemas import MovementListItem
        return [
            MovementListItem(
                id=r[0], code=r[1], consecutive=r[2],
                item_id=r[3], item_code=r[4], item_name=r[5],
                movement_type=r[6], quantity=r[7], unit_cost=r[8],
                reason=r[9], movement_date=r[10], created_at=r[11],
            )
            for r in rows.all()
        ]
