"""Business logic for SavvyPay transactions — state machine + ledger integration."""

from __future__ import annotations
import uuid
from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.exceptions import ConflictError, NotFoundError, ValidationError
from src.apps.pay.transactions.models import PayRefund, PayTransaction
from src.apps.pay.transactions.schemas import RefundCreate, TransactionAction, TransactionCreate
from src.apps.pay.ledger.service import LedgerEngine
from src.apps.pay.ledger.schemas import JournalCreate, LedgerEntryLine

# Valid state transitions
VALID_TRANSITIONS = {
    "pending": {"authorized", "captured", "failed", "cancelled"},
    "authorized": {"captured", "failed", "cancelled"},
    "captured": {"settled", "refunded"},
    "settled": {"refunded"},
}


class TransactionService:

    @staticmethod
    async def create_transaction(
        db: AsyncSession, org_id: uuid.UUID, data: TransactionCreate,
    ) -> PayTransaction:
        # Check idempotency
        if data.idempotency_key:
            existing = await db.execute(
                select(PayTransaction).where(PayTransaction.idempotency_key == data.idempotency_key)
            )
            if existing.scalar_one_or_none():
                raise ConflictError("Duplicate transaction: idempotency key already used.")

        tx = PayTransaction(
            organization_id=org_id,
            idempotency_key=data.idempotency_key,
            transaction_type=data.transaction_type,
            amount=data.amount,
            currency=data.currency,
            net_amount=data.amount,  # fees applied later
            payer_account_id=data.payer_account_id,
            payee_account_id=data.payee_account_id,
            payment_method=data.payment_method,
            source_app=data.source_app,
            source_ref_type=data.source_ref_type,
            source_ref_id=data.source_ref_id,
            description=data.description,
            metadata_=data.metadata,
        )
        db.add(tx)
        await db.flush()
        await db.refresh(tx)

        # Emit event
        await LedgerEngine.emit_event(db, org_id, "payment.created", "transaction", tx.id,
            {"amount": data.amount, "currency": data.currency, "type": data.transaction_type},
            source_app=data.source_app)

        return tx

    @staticmethod
    async def transition(
        db: AsyncSession, org_id: uuid.UUID, tx_id: uuid.UUID, action: TransactionAction,
    ) -> PayTransaction:
        """Move a transaction through its state machine."""
        result = await db.execute(
            select(PayTransaction).where(PayTransaction.id == tx_id, PayTransaction.organization_id == org_id)
        )
        tx = result.scalar_one_or_none()
        if tx is None:
            raise NotFoundError("Transaction not found.")

        target_status = action.action
        if target_status == "authorize":
            target_status = "authorized"
        elif target_status == "capture":
            target_status = "captured"
        elif target_status == "settle":
            target_status = "settled"
        elif target_status == "fail":
            target_status = "failed"
        elif target_status == "cancel":
            target_status = "cancelled"

        valid = VALID_TRANSITIONS.get(tx.status, set())
        if target_status not in valid:
            raise ValidationError(f"Cannot transition from '{tx.status}' to '{target_status}'.")

        now = datetime.now(UTC)
        tx.status = target_status

        if target_status == "authorized":
            tx.authorized_at = now
        elif target_status == "captured":
            tx.captured_at = now
            # Post ledger entries on capture: debit payer, credit payee
            if tx.payer_account_id and tx.payee_account_id:
                await LedgerEngine.post_journal(db, org_id, JournalCreate(
                    lines=[
                        LedgerEntryLine(account_id=tx.payee_account_id, entry_type="debit", amount=tx.amount, description=f"Payment captured: {tx.description}"),
                        LedgerEntryLine(account_id=tx.payer_account_id, entry_type="credit", amount=tx.amount, description=f"Payment captured: {tx.description}"),
                    ],
                    transaction_id=tx.id, source_app=tx.source_app,
                    idempotency_key=f"capture_{tx.id}",
                ))
        elif target_status == "settled":
            tx.settled_at = now
        elif target_status == "failed":
            tx.failed_at = now
            tx.failure_reason = action.failure_reason

        await db.flush()
        await db.refresh(tx)

        await LedgerEngine.emit_event(db, org_id, f"payment.{target_status}", "transaction", tx.id,
            {"status": target_status, "amount": float(tx.amount)}, source_app=tx.source_app)

        return tx

    @staticmethod
    async def list_transactions(
        db: AsyncSession, org_id: uuid.UUID,
        status_filter: str | None = None, tx_type: str | None = None, limit: int = 50,
    ) -> list[PayTransaction]:
        q = select(PayTransaction).where(PayTransaction.organization_id == org_id)
        if status_filter:
            q = q.where(PayTransaction.status == status_filter)
        if tx_type:
            q = q.where(PayTransaction.transaction_type == tx_type)
        return list((await db.execute(q.order_by(PayTransaction.created_at.desc()).limit(limit))).scalars().all())

    @staticmethod
    async def get_transaction(db: AsyncSession, org_id: uuid.UUID, tx_id: uuid.UUID) -> PayTransaction:
        result = await db.execute(select(PayTransaction).where(PayTransaction.id == tx_id, PayTransaction.organization_id == org_id))
        tx = result.scalar_one_or_none()
        if tx is None:
            raise NotFoundError("Transaction not found.")
        return tx

    @staticmethod
    async def create_refund(db: AsyncSession, org_id: uuid.UUID, data: RefundCreate) -> PayRefund:
        tx = await TransactionService.get_transaction(db, org_id, data.transaction_id)
        if tx.status not in ("captured", "settled"):
            raise ValidationError("Can only refund captured or settled transactions.")

        total_refunded = Decimal(str(tx.refunded_amount)) + Decimal(str(data.amount))
        if total_refunded > Decimal(str(tx.amount)):
            raise ValidationError("Refund amount exceeds transaction amount.")

        refund = PayRefund(
            organization_id=org_id, transaction_id=tx.id,
            amount=data.amount, reason=data.reason,
            idempotency_key=data.idempotency_key, status="processed",
            processed_at=datetime.now(UTC),
        )
        db.add(refund)
        tx.refunded_amount = float(total_refunded)
        if total_refunded >= Decimal(str(tx.amount)):
            tx.status = "refunded"

        # Reverse ledger entries
        if tx.payer_account_id and tx.payee_account_id:
            await LedgerEngine.post_journal(db, org_id, JournalCreate(
                lines=[
                    LedgerEntryLine(account_id=tx.payer_account_id, entry_type="debit", amount=data.amount, description=f"Refund: {data.reason}"),
                    LedgerEntryLine(account_id=tx.payee_account_id, entry_type="credit", amount=data.amount, description=f"Refund: {data.reason}"),
                ],
                transaction_id=tx.id, source_app=tx.source_app,
                idempotency_key=data.idempotency_key or f"refund_{refund.id}",
            ))

        await db.flush()
        await db.refresh(refund)

        await LedgerEngine.emit_event(db, org_id, "payment.refunded", "transaction", tx.id,
            {"refund_amount": data.amount, "total_refunded": float(total_refunded)})
        return refund
